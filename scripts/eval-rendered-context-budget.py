#!/usr/bin/env python3
"""Exact token and admissible JIT-context measurement of built instructions."""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unicodedata
from collections import Counter, defaultdict
from contextlib import contextmanager
from itertools import combinations
from pathlib import Path, PurePosixPath
from typing import Any
from validation_utils import (
    BEHAVIOR_EVAL_MODEL,
    COMPILED_LAYER3_FORMAT,
    CONTEXT_BUDGET_MODEL,
    CORE_CONTRACTS,
    RUNTIME_ASSET_LAYER3_MARKER_TEMPLATE,
    RUNTIME_ASSET_PROFESSIONAL_JIT_TEMPLATE,
    ValidationProblem,
    authoritative_build_input_snapshot,
    behavior_eval_authority,
    count_o200k_base_tokens,
    derived_context_budget_limits,
    layer3_selector_authority,
    layer3_selector_control_projections,
    layer3_selector_expand_runtime_projection,
    layer3_selector_resolve_control_projection,
    layer3_selector_runtime_projection,
    layer3_selector_runtime_selection_receipt,
    layer3_selector_runtime_selection_receipt_errors,
    load_yaml_file,
    parse_frontmatter,
    reference_context_admissibility_authority,
    reference_context_admissibility_decisions,
    reference_context_staged_plan,
    reference_paths,
    report_output_paths,
    runtime_asset_build_identity,
    runtime_reference_record_target,
)
from fixture_capsule_contract import FixtureCapsuleError, runtime_layer3_reference_path, validate_and_render_fixture_capsule
ROOT = Path(__file__).resolve().parents[1]


FIXTURES = ROOT / "evals" / "agent-light-trajectories" / "cases.yaml"


DIST_SKILLS = ROOT / "dist" / "universal" / "skills"


CONTROL_PROMPT = ROOT / "src" / "control-prompts" / "main-control-agent.md"


REPORT_JSON = ROOT / "reports" / "rendered-context-budget.json"


REPORT_MD = ROOT / "reports" / "rendered-context-budget.md"


LIGHTWEIGHT_REPORT = ROOT / "reports" / "hookless-control-plane-eval.json"


IMPLEMENTATION_HANDOFF_TEMPLATE = (
    ROOT
    / "src"
    / "control-skills"
    / "engineering-control-plane"
    / "references"
    / "implementation-handoff-template.md"
)


REVIEW_HANDOFF_TEMPLATE = IMPLEMENTATION_HANDOFF_TEMPLATE.with_name(
    "review-handoff-template.md"
)


PROFESSIONAL_REGISTRY = ROOT / "src" / "registry" / "professional-skills.yaml"


FOUNDATION_REGISTRY = ROOT / "src" / "registry" / "foundation-skills.yaml"


DOMAIN_REGISTRY = ROOT / "src" / "registry" / "domain-skills.yaml"


RUNTIME_NAME = "recommended"


HOST_PROFILE_ROOTS = {
    "codex": ROOT / "dist" / "codex" / "project" / ".codex" / "agents",
    "claude": ROOT / "dist" / "claude" / "project" / ".claude" / "agents",
    "copilot": ROOT / "dist" / "copilot" / "project" / ".github" / "agents",
}


HOST_PROFILE_SUFFIXES = {
    "codex": ".toml",
    "claude": ".md",
    "copilot": ".agent.md",
}


@contextmanager
def _subject_configuration(
    root: Path,
    fixtures: Path,
    lightweight_report: Path,
):
    global ROOT, FIXTURES, DIST_SKILLS, CONTROL_PROMPT, LIGHTWEIGHT_REPORT
    global IMPLEMENTATION_HANDOFF_TEMPLATE, REVIEW_HANDOFF_TEMPLATE
    global PROFESSIONAL_REGISTRY, FOUNDATION_REGISTRY, DOMAIN_REGISTRY
    global HOST_PROFILE_ROOTS
    names = (
        "ROOT",
        "FIXTURES",
        "DIST_SKILLS",
        "CONTROL_PROMPT",
        "LIGHTWEIGHT_REPORT",
        "IMPLEMENTATION_HANDOFF_TEMPLATE",
        "REVIEW_HANDOFF_TEMPLATE",
        "PROFESSIONAL_REGISTRY",
        "FOUNDATION_REGISTRY",
        "DOMAIN_REGISTRY",
        "HOST_PROFILE_ROOTS",
    )
    saved = {name: globals()[name] for name in names}
    ROOT = root.resolve()
    FIXTURES = fixtures.resolve()
    DIST_SKILLS = ROOT / "dist/universal/skills"
    CONTROL_PROMPT = ROOT / "src/control-prompts/main-control-agent.md"
    LIGHTWEIGHT_REPORT = lightweight_report.resolve()
    IMPLEMENTATION_HANDOFF_TEMPLATE = ROOT / (
        "src/control-skills/engineering-control-plane/references/"
        "implementation-handoff-template.md"
    )
    REVIEW_HANDOFF_TEMPLATE = IMPLEMENTATION_HANDOFF_TEMPLATE.with_name(
        "review-handoff-template.md"
    )
    PROFESSIONAL_REGISTRY = ROOT / "src/registry/professional-skills.yaml"
    FOUNDATION_REGISTRY = ROOT / "src/registry/foundation-skills.yaml"
    DOMAIN_REGISTRY = ROOT / "src/registry/domain-skills.yaml"
    HOST_PROFILE_ROOTS = {
        "codex": ROOT / "dist/codex/project/.codex/agents",
        "claude": ROOT / "dist/claude/project/.claude/agents",
        "copilot": ROOT / "dist/copilot/project/.github/agents",
    }
    try:
        yield
    finally:
        globals().update(saved)


CONTEXT_BUDGET_LIMITS = derived_context_budget_limits(CONTEXT_BUDGET_MODEL)


DISPATCH_COMPOSITION_CLASSES = tuple(
    CONTEXT_BUDGET_MODEL["context_taxonomy"]["dispatch_composition"]["classes"]
)


ADMISSIBLE_BUDGET_CLASSES = tuple(
    budget_class
    for budget_class in DISPATCH_COMPOSITION_CLASSES
    if budget_class != "utility"
)


ADMISSIBLE_COMPOSITION_CONTRACT = (
    "changeforge.admissible-context-composition-eval/v1"
)


CONTEXT_COMPONENT_SEPARATOR_TOKENS = count_o200k_base_tokens("\n\n")


DUPLICATE_TOKEN_RATIO_MAX = CONTEXT_BUDGET_MODEL[
    "duplicate_rule_token_ratio_max"
]


MIN_DUPLICATE_BLOCK_CHARS = 50


MIN_DUPLICATE_BLOCK_TOKENS = 12


MODE_REFERENCES = {
    "implementation-preparation": "references/implementation-preparation.md",
    "diagnosis-only": "references/diagnosis-only.md",
    "source-backed-answer": "references/source-backed-answer.md",
}


LIMITATIONS = (
    "Counts cover deterministic rendered rd-skills instructions and canonical Capsules rendered from versioned checked-in fixture data, not a host-observed model request.",
    "Counts exclude host system prompts, tool schemas, user conversation history, repository reads, diffs, command output, and other dynamic evidence.",
    "Host loaders may transform Profile or Skill files and may expose discovery metadata differently; this report does not prove real-host accuracy.",
    "Token counts do not prove wall-clock performance, production accuracy, Profile startup, or the installed user experience.",
    "Duplicate-token measurement detects exact normalized Markdown rule blocks, not semantic paraphrases.",
    "Nested Layer 3 Reference counts include only explicitly named fixture files; directories, indexes, catalogs, and recursively linked files are never loaded.",
)


FIXTURE_SCHEMA_VERSION = 2


_LIST_ITEM_RE = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+(.*)$")


_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}(?:\s+|$)")


_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?(?:\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$")


_HTML_COMMENT_RE = re.compile(r"^\s*<!--.*?-->\s*$")


_MARKDOWN_LINK_RE = re.compile(r"\[([^]]+)\]\([^)]+\)")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _component(kind: str, path: str, text: str) -> dict[str, Any]:
    return {
        "kind": kind,
        "path": path,
        "sha256": _sha256_text(text),
        "tokens": count_o200k_base_tokens(text),
        "_text": text,
    }


def _file_component(kind: str, path: Path) -> dict[str, Any]:
    return _component(kind, _relative(path), path.read_text(encoding="utf-8"))


def _strip_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[index + 1 :])
    return text


def _normalize_rule_block(block: str) -> str:
    value = unicodedata.normalize("NFKC", block)
    value = _MARKDOWN_LINK_RE.sub(r"\1", value)
    value = re.sub(r"[`*_~>]", "", value)
    value = " ".join(value.casefold().split())
    return value.strip()


def _markdown_rule_blocks(text: str) -> list[str]:
    """Return non-overlapping normalized prose/list blocks for exact copy checks."""

    blocks: list[str] = []
    current: list[str] = []
    in_fence = False

    def flush() -> None:
        if not current:
            return
        normalized = _normalize_rule_block(" ".join(current))
        current.clear()
        if len(normalized) < MIN_DUPLICATE_BLOCK_CHARS:
            return
        if count_o200k_base_tokens(normalized) < MIN_DUPLICATE_BLOCK_TOKENS:
            return
        blocks.append(normalized)

    for raw_line in _strip_frontmatter(text).splitlines():
        stripped = raw_line.strip()
        if stripped.startswith(("```", "~~~")):
            flush()
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not stripped:
            flush()
            continue
        if (
            _HEADING_RE.match(raw_line)
            or _HTML_COMMENT_RE.match(raw_line)
            or _TABLE_SEPARATOR_RE.match(raw_line)
            or (stripped.startswith("|") and stripped.endswith("|"))
        ):
            flush()
            continue
        list_match = _LIST_ITEM_RE.match(raw_line)
        if list_match:
            flush()
            current.append(list_match.group(1))
            continue
        current.append(stripped)
    flush()
    return blocks


def _duplicate_block_metrics(components: list[dict[str, Any]]) -> dict[str, Any]:
    occurrences: dict[str, list[str]] = defaultdict(list)
    for component in components:
        component_id = f"{component['kind']}:{component['path']}"
        for block in _markdown_rule_blocks(component["_text"]):
            occurrences[block].append(component_id)

    duplicate_tokens = 0
    duplicate_blocks: list[dict[str, Any]] = []
    for block, source_occurrences in occurrences.items():
        if len(source_occurrences) < 2:
            continue
        block_tokens = count_o200k_base_tokens(block)
        repeated_tokens = block_tokens * (len(source_occurrences) - 1)
        source_counts: dict[str, int] = defaultdict(int)
        for source in source_occurrences:
            source_counts[source] += 1
        duplicate_tokens += repeated_tokens
        duplicate_blocks.append(
            {
                "sha256": _sha256_text(block),
                "tokens_per_extra_copy": block_tokens,
                "occurrence_count": len(source_occurrences),
                "extra_copy_count": len(source_occurrences) - 1,
                "duplicate_tokens": repeated_tokens,
                "sources": [
                    {"component": source, "occurrences": count}
                    for source, count in sorted(source_counts.items())
                ],
                "preview": block[:160],
            }
        )
    duplicate_blocks.sort(
        key=lambda item: (-item["duplicate_tokens"], item["sha256"])
    )
    return {
        "duplicate_rule_tokens": duplicate_tokens,
        "duplicate_blocks": duplicate_blocks,
    }


def _canonical_json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _measure_context(
    components: list[dict[str, Any]],
    *,
    budget_class: str,
) -> dict[str, Any]:
    limit = CONTEXT_BUDGET_LIMITS[budget_class]
    combined = "\n\n".join(component["_text"].rstrip() for component in components)
    total_tokens = count_o200k_base_tokens(combined)
    duplicates = _duplicate_block_metrics(components)
    duplicate_tokens = duplicates["duplicate_rule_tokens"]
    ratio = duplicate_tokens / total_tokens if total_tokens else 0.0
    public_components = [
        {key: value for key, value in component.items() if key != "_text"}
        for component in components
    ]
    within_soft_target = total_tokens <= limit["soft_target"]
    within_hard_ceiling = total_tokens <= limit["hard_ceiling"]
    return {
        "budget_class": budget_class,
        "soft_target": limit["soft_target"],
        "hard_ceiling": limit["hard_ceiling"],
        "calibration_status": limit["calibration_status"],
        "total_tokens": total_tokens,
        "sum_component_tokens": sum(item["tokens"] for item in public_components),
        "duplicate_rule_tokens": duplicate_tokens,
        "duplicate_rule_token_ratio": round(ratio, 6),
        "within_soft_target": within_soft_target,
        "within_hard_ceiling": within_hard_ceiling,
        "soft_margin_tokens": limit["soft_target"] - total_tokens,
        "hard_margin_tokens": limit["hard_ceiling"] - total_tokens,
        "budget_signal": (
            "hard-ceiling-exceeded"
            if not within_hard_ceiling
            else "growth-advisory"
            if not within_soft_target
            else None
        ),
        "within_duplicate_budget": ratio <= DUPLICATE_TOKEN_RATIO_MAX,
        "components": public_components,
        "duplicate_blocks": duplicates["duplicate_blocks"],
    }


def evaluate_route_obligation_context(
    components: list[dict[str, Any]],
    *,
    required_route_obligations: dict[str, Any],
    budget_class: str,
) -> dict[str, Any]:
    """Evaluate token pressure while preserving one closed route obligation input."""

    required_fields = {
        "primary_professional_skill",
        "implementation_layer3",
        "domain",
        "required_review_skills",
    }
    if (
        not isinstance(required_route_obligations, dict)
        or set(required_route_obligations) != required_fields
        or not isinstance(
            required_route_obligations["primary_professional_skill"], str
        )
        or not required_route_obligations["primary_professional_skill"]
        or any(
            not isinstance(required_route_obligations[field], list)
            or any(
                not isinstance(item, str) or not item
                for item in required_route_obligations[field]
            )
            for field in (
                "implementation_layer3",
                "domain",
                "required_review_skills",
            )
        )
    ):
        raise ValueError("route obligations must use the exact closed contract")
    obligation_components = [
        component
        for component in components
        if isinstance(component, dict)
        and component.get("kind") == "route-obligations"
    ]
    observed: object = None
    if len(obligation_components) == 1:
        try:
            observed = json.loads(obligation_components[0]["_text"])
        except (KeyError, TypeError, json.JSONDecodeError):
            observed = None
    preserved = observed == required_route_obligations
    if not preserved:
        return {
            "failure_id": "context-route-obligation-mismatch",
            "outcome": "fail-closed",
            "continue_allowed": False,
            "route_obligations_preserved": False,
            "required_route_obligations": required_route_obligations,
            "observed_route_obligations": observed,
        }
    measurement = _measure_context(
        components,
        budget_class=budget_class,
    )
    overflow = measurement["within_hard_ceiling"] is False
    return {
        **measurement,
        "failure_id": (
            "context-token-budget-overflow" if overflow else None
        ),
        "outcome": "fail-closed" if overflow else "continue",
        "continue_allowed": not overflow,
        "route_obligations_preserved": True,
        "required_route_obligations": required_route_obligations,
        "observed_route_obligations": observed,
    }


def _profile_path(host: str, role: str) -> Path:
    return HOST_PROFILE_ROOTS[host] / f"{role}{HOST_PROFILE_SUFFIXES[host]}"


def _load_runtime_manifest(errors: list[str]) -> dict[str, Any] | None:
    path = DIST_SKILLS / RUNTIME_NAME / ".changeforge-build-manifest.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(
            f"{_relative(path)} is unavailable or malformed; run the Runtime build first: {exc}"
        )
        return None
    if not isinstance(value, dict) or value.get("profile") != RUNTIME_NAME:
        errors.append(f"{_relative(path)} does not describe Runtime {RUNTIME_NAME!r}")
        return None
    if value.get("compiled_layer3_format") != COMPILED_LAYER3_FORMAT:
        errors.append(
            f"{_relative(path)} compiled_layer3_format must equal "
            f"{COMPILED_LAYER3_FORMAT!r}"
        )
        return None
    top_level = value.get("top_level_skills")
    control = value.get("control_skills")
    professional = value.get("professional_skills")
    foundation = value.get("foundation_skills")
    domain = value.get("domain_skills")
    if not all(
        isinstance(items, list)
        and all(isinstance(item, str) and item for item in items)
        for items in (top_level, control, professional, foundation, domain)
    ):
        errors.append(f"{_relative(path)} has malformed Runtime inventory lists")
        return None
    expected_top_level = [*control, *professional]
    if (
        len(top_level) != 26
        or len(top_level) != len(set(top_level))
        or set(top_level) != set(expected_top_level)
        or set(top_level) & (set(foundation) | set(domain))
    ):
        errors.append(
            f"{_relative(path)} Runtime discovery must contain exactly one Control "
            "and 25 Professional Skills with no Foundation or Domain top-level Skill"
        )
        return None
    return value


def _validate_profile_digest(
    host: str,
    role: str,
    profile_path: Path,
    manifest: dict[str, Any],
    errors: list[str],
) -> None:
    expected = (
        manifest.get("agent_profile_sha256", {})
        .get(host, {})
        .get(role)
    )
    actual = hashlib.sha256(profile_path.read_bytes()).hexdigest()
    if expected != actual:
        errors.append(
            f"{_relative(profile_path)} digest does not match the {manifest.get('profile')} build manifest"
        )


def _layer3_path(
    runtime_name: str,
    primary: str,
    name: str,
    manifest: dict[str, Any],
) -> Path:
    compiled = manifest.get("compiled_layer3_references", {}).get(primary, [])
    is_compiled = name in compiled
    is_top_level = name in manifest.get("top_level_skills", [])
    if is_compiled == is_top_level:
        raise ValueError(
            f"{runtime_name}:{primary} must resolve routed Layer 3 Skill {name!r} "
            "through exactly one compiled or top-level delivery path"
        )
    if is_compiled:
        return DIST_SKILLS / runtime_name / primary / "references" / "layer3" / f"{name}.md"
    return DIST_SKILLS / runtime_name / name / "SKILL.md"


def _runtime_reference_partition(
    professional_root: Path,
    primary: str,
    owner: str,
) -> dict[str, Any]:
    partition_path = (
        professional_root
        / "references/runtime/reference-records"
        / f"{owner}.json"
    )
    if partition_path.is_symlink() or not partition_path.is_file():
        raise ValueError(
            f"{primary}: Runtime Reference partition for {owner!r} is missing or symlinked"
        )
    try:
        partition = json.loads(partition_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"{primary}: Runtime Reference partition for {owner!r} is unreadable"
        ) from exc
    if (
        not isinstance(partition, dict)
        or partition.get("professional_skill") != primary
        or partition.get("owner_skill") != owner
        or not isinstance(partition.get("reference_records"), list)
    ):
        raise ValueError(
            f"{primary}: Runtime Reference partition for {owner!r} is malformed"
        )
    return partition


def _runtime_reference_record(
    professional_root: Path,
    primary: str,
    record_path: str,
) -> dict[str, Any]:
    """Select only the exact record named by the Runtime ``path`` field."""

    parsed = PurePosixPath(record_path)
    if parsed.parts[:2] == ("references", "layer3"):
        runtime_layer3_reference_path(record_path)
        owner = parsed.parts[2]
    elif (
        not parsed.is_absolute()
        and len(parsed.parts) == 2
        and parsed.parts[0] == "references"
        and re.fullmatch(r"[a-z0-9][a-z0-9.-]*\.md", parsed.parts[1])
    ):
        owner = primary
    else:
        raise ValueError(
            f"{primary}: Runtime Reference path is not one exact generated record path"
        )
    partition = _runtime_reference_partition(professional_root, primary, owner)
    matches = [
        record
        for record in partition["reference_records"]
        if isinstance(record, dict) and record.get("path") == record_path
    ]
    if len(matches) != 1:
        raise ValueError(
            f"{primary}: Runtime Reference path {record_path!r} does not name one record"
        )
    return matches[0]


def _runtime_reference_record_and_target(
    professional_root: Path,
    primary: str,
    record_path: str,
) -> tuple[dict[str, Any], Path]:
    """Resolve only an exact generated record ``path`` under one root."""

    record = _runtime_reference_record(
        professional_root,
        primary,
        record_path,
    )
    try:
        target = runtime_reference_record_target(
            professional_root,
            record,
            expected_professional_skill=primary,
            context=f"{primary}: Runtime Reference {record_path}",
        )
    except ValidationProblem as exc:
        raise ValueError(str(exc)) from exc
    return record, target


def _runtime_reference_target_for_authoring_entry(
    runtime_name: str,
    primary: str,
    owner: str,
    entry: dict[str, Any],
) -> tuple[str, Path]:
    """Compare source authority to Build output without projecting its path."""

    professional_root = DIST_SKILLS / runtime_name / primary
    partition = _runtime_reference_partition(professional_root, primary, owner)
    semantic_fields = (
        "type",
        "load_when",
        "do_not_load_when",
        "required_by",
        "required_output",
    )
    matches = [
        record
        for record in partition["reference_records"]
        if isinstance(record, dict)
        and record.get("owner_skill") == owner
        and all(record.get(field) == entry.get(field) for field in semantic_fields)
    ]
    if len(matches) != 1:
        raise ValueError(
            f"{primary}:{owner}: source Reference does not bind one Runtime record"
        )
    record = matches[0]
    try:
        target = runtime_reference_record_target(
            professional_root,
            record,
            expected_professional_skill=primary,
            context=f"{primary}:{owner}: Runtime Reference",
        )
    except ValidationProblem as exc:
        raise ValueError(str(exc)) from exc
    return str(record["path"]), target


def _uses_symlink(path: Path, boundary: Path) -> bool:
    current = path
    while current != boundary and boundary in current.parents:
        if current.is_symlink():
            return True
        current = current.parent
    return current.is_symlink()


def _layer3_reference_registry_errors(
    case_id: str,
    index: int,
    step: dict[str, Any],
) -> list[str]:
    if "utility_capsule" in step:
        return []
    raw = step.get("layer3_references")
    if not isinstance(raw, list):
        return [f"{case_id}: dispatch step {index} layer3_references must be a list"]
    errors: list[str] = []
    selected = step.get("layer3_skills")
    if not isinstance(selected, list):
        return [f"{case_id}: dispatch step {index} layer3_skills must be a list"]
    for raw_path in raw:
        try:
            record_path = runtime_layer3_reference_path(raw_path)
        except FixtureCapsuleError as exc:
            errors.append(f"{case_id}: dispatch step {index}: {exc}")
            continue
        owner = PurePosixPath(record_path).parts[2]
        if owner not in selected:
            errors.append(
                f"{case_id}: dispatch step {index} Layer 3 Reference "
                f"{record_path!r} owner is not selected"
            )
    return errors


def _budget_class(step, case_kind, case_steps):
    role = step.get("profile")
    if role == "analysis-agent": return "analysis"
    if role == "review-agent": return "review"
    if role == "task-agent": return "analyzed_task" if step.get("brief") else "task"
    raise ValueError(f"unsupported dispatch profile {role!r}")


def _fixture_cases(document):
    cases = document.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("non-empty behavior cases required")
    return [("behavior", case) for case in cases]


def _dispatch_metadata_errors(case_id, index, step, steps=None):
    try:
        validate_and_render_fixture_capsule(step)
    except (FixtureCapsuleError, TypeError) as exc:
        return [f"{case_id}: dispatch {index}: {exc}"]
    return []


def _discovery_metadata(
    runtime_name: str,
    errors: list[str],
) -> dict[str, Any]:
    root = DIST_SKILLS / runtime_name
    entries: list[dict[str, Any]] = []
    payloads: list[str] = []
    for skill_dir in sorted(
        path for path in root.iterdir() if path.is_dir() and not path.name.startswith(".")
    ):
        skill_file = skill_dir / "SKILL.md"
        try:
            metadata, _raw, _body = parse_frontmatter(skill_file)
        except ValidationProblem as exc:
            errors.append(str(exc).replace(str(ROOT) + "/", ""))
            continue
        name = metadata.get("name")
        description = metadata.get("description")
        if not isinstance(name, str) or not isinstance(description, str):
            errors.append(f"{_relative(skill_file)} lacks name/description discovery metadata")
            continue
        payload = f"name: {name}\ndescription: {description.strip()}"
        payloads.append(payload)
        entries.append(
            {
                "path": _relative(skill_file),
                "sha256": _sha256_text(payload),
                "tokens": count_o200k_base_tokens(payload),
            }
        )
    combined = "\n\n".join(payloads)
    return {
        "runtime": runtime_name,
        "skill_count": len(entries),
        "canonical_serialization": "name and description from each top-level SKILL.md",
        "tokens": count_o200k_base_tokens(combined),
        "sha256": _sha256_text(combined),
        "entries": entries,
        "accounting": "reported separately because host discovery injection is not observed",
    }


def _compact_component_catalog(
    contexts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Deduplicate repeated host/profile/Skill component evidence in the report."""

    keys = sorted(
        {
            (
                component["kind"],
                component["path"],
                component["sha256"],
                component["tokens"],
            )
            for context in contexts
            for component in context.get("components", [])
        }
    )
    ids = {key: f"component-{index:04d}" for index, key in enumerate(keys, start=1)}
    catalog = [
        {
            "id": ids[key],
            "kind": key[0],
            "path": key[1],
            "sha256": key[2],
            "tokens": key[3],
        }
        for key in keys
    ]
    for context in contexts:
        context["component_ids"] = [
            ids[
                (
                    component["kind"],
                    component["path"],
                    component["sha256"],
                    component["tokens"],
                )
            ]
            for component in context.pop("components", [])
        ]
        context.pop("duplicate_blocks", None)
    return catalog


def _maximum_summary(
    maximum: dict[str, Any] | None,
    *,
    include_dispatch: bool,
) -> dict[str, Any] | None:
    """Expose Core-derived soft and hard margins for one maximum."""

    if maximum is None:
        return None
    observed = maximum["total_tokens"]
    result = {
        "tokens": observed,
        "soft_target": maximum["soft_target"],
        "hard_ceiling": maximum["hard_ceiling"],
        "soft_margin_tokens": maximum["soft_target"] - observed,
        "hard_margin_tokens": maximum["hard_ceiling"] - observed,
        "within_soft_target": maximum["within_soft_target"],
        "within_hard_ceiling": maximum["within_hard_ceiling"],
        "budget_signal": maximum["budget_signal"],
        "calibration_status": maximum["calibration_status"],
        "host": maximum["host"],
        "runtime": maximum["runtime"],
    }
    if include_dispatch:
        result.update(
            {
                "step": maximum["step"],
                "primary_skill": maximum["primary_skill"],
            }
        )
    return result


def _selector_authority() -> dict[str, Any]:
    """Load the single registry-owned selector authority projection."""

    return layer3_selector_authority(
        load_yaml_file(FOUNDATION_REGISTRY),
        load_yaml_file(PROFESSIONAL_REGISTRY),
        load_yaml_file(DOMAIN_REGISTRY),
        context="admissible context composition selector authority",
    )


def _normalized_signal(value: str) -> str:
    return " ".join(value.casefold().split())


def _activation_evidence(records: tuple[dict[str, Any], ...]) -> list[str] | None:
    """Choose one source-declared representative for a selector equivalence class."""

    negatives = {
        _normalized_signal(signal)
        for record in records
        for signal in record["nearest_negative_signals"]
    }
    evidence: list[str] = []
    normalized_evidence: set[str] = set()
    for record in records:
        for group in record["positive_signal_groups"]:
            selected = next(
                (
                    signal
                    for signal in group
                    if _normalized_signal(signal) not in negatives
                ),
                None,
            )
            if selected is None:
                return None
            normalized = _normalized_signal(selected)
            if normalized not in normalized_evidence:
                normalized_evidence.add(normalized)
                evidence.append(selected)
    return evidence


def _selection_kind(profile: str) -> str:
    return {
        "analysis-agent": "analysis-risk",
        "task-agent": "implementation-risk",
        "review-agent": "review-risk",
    }[profile]


def _admissible_selector_equivalence_classes(
    authority: dict[str, Any],
    projection: dict[str, Any],
    build_identity: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, int], list[str]]:
    """Invoke the canonical selector over every legal <=3 activation class."""

    if build_identity is None:
        runtime_manifest = json.loads(
            (
                DIST_SKILLS
                / RUNTIME_NAME
                / ".changeforge-build-manifest.json"
            ).read_text(encoding="utf-8")
        )
        full_digest = runtime_manifest.get("authoritative_build_inputs", {}).get(
            "sha256"
        )
        if (
            not isinstance(full_digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", full_digest) is None
        ):
            raise ValueError("admissible selector build identity is missing")
        build_identity = runtime_asset_build_identity(full_digest)
    errors: list[str] = []
    selectors = projection["selectors"]
    classes_by_selected: dict[tuple[str, ...], dict[str, Any]] = {}
    positive_cases = 0
    nearest_negative_cases = 0
    nearest_negative_leaks = 0
    over_max_rejections = 0
    unauthorized_exact_rejections = 0
    duplicate_exact_rejections = 0

    empty_receipt = layer3_selector_runtime_selection_receipt(
        projection,
        evidence_signals=[],
        build_identity=build_identity,
    )
    classes_by_selected[tuple(empty_receipt["selected_layer3"])] = {
        "selected_layer3": list(empty_receipt["selected_layer3"]),
        "receipt": empty_receipt,
    }

    for record in selectors:
        evidence = _activation_evidence((record,))
        if evidence is None:
            errors.append(
                f"{projection['professional_skill']}:{projection['profile']}:"
                f"{record['selector_id']} has no positive representative outside "
                "its nearest-negative boundary"
            )
            continue
        positive_cases += 1
        receipt = layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=evidence,
            build_identity=build_identity,
        )
        classes_by_selected.setdefault(
            tuple(receipt["selected_layer3"]),
            {
                "selected_layer3": list(receipt["selected_layer3"]),
                "receipt": receipt,
            },
        )
        negative_evidence = [*evidence, record["nearest_negative_signals"][0]]
        negative_receipt = layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=negative_evidence,
            build_identity=build_identity,
        )
        nearest_negative_cases += 1
        if set(record["selectable_layer3"]) & set(
            negative_receipt["selected_layer3"]
        ):
            nearest_negative_leaks += 1

    for size in range(2, min(3, len(selectors)) + 1):
        for selected_records in combinations(selectors, size):
            evidence = _activation_evidence(selected_records)
            if evidence is None:
                continue
            try:
                receipt = layer3_selector_runtime_selection_receipt(
                    projection,
                    evidence_signals=evidence,
                    build_identity=build_identity,
                )
            except ValidationProblem as exc:
                if "more than three Layer 3" not in str(exc):
                    errors.append(str(exc))
                continue
            classes_by_selected.setdefault(
                tuple(receipt["selected_layer3"]),
                {
                    "selected_layer3": list(receipt["selected_layer3"]),
                    "receipt": receipt,
                },
            )

    for selected_class in classes_by_selected.values():
        selected = selected_class["selected_layer3"]
        try:
            fixed = layer3_selector_runtime_projection(
                authority,
                professional_skill=projection["professional_skill"],
                profile=projection["profile"],
                selection_owner=projection["selection_owner"],
                exact_layer3=selected,
            )
        except ValidationProblem as exc:
            errors.append(str(exc))
            continue
        if fixed["selector_loaded"] or fixed["exact_layer3"] != selected:
            errors.append(
                f"{projection['professional_skill']}:{projection['profile']} "
                "exact Layer 3 did not skip selector loading"
            )

    replay_class = max(
        classes_by_selected.values(),
        key=lambda item: len(item["selected_layer3"]),
    )
    replay_errors = layer3_selector_runtime_selection_receipt_errors(
        replay_class["receipt"],
        expected_owner=projection["selection_owner"],
        expected_profile=projection["profile"],
        expected_professional=projection["professional_skill"],
        expected_selection_kind=_selection_kind(projection["profile"]),
        expected_selected_layer3=replay_class["selected_layer3"],
        expected_build_identity=build_identity,
    )
    errors.extend(replay_errors)

    try:
        layer3_selector_runtime_projection(
            authority,
            professional_skill=projection["professional_skill"],
            profile=projection["profile"],
            selection_owner=projection["selection_owner"],
            exact_layer3=["admissible-context-invented-layer3"],
        )
    except ValidationProblem:
        unauthorized_exact_rejections += 1
    authorized = projection["authorized_layer3"]
    if authorized:
        try:
            layer3_selector_runtime_projection(
                authority,
                professional_skill=projection["professional_skill"],
                profile=projection["profile"],
                selection_owner=projection["selection_owner"],
                exact_layer3=[authorized[0], authorized[0]],
            )
        except ValidationProblem:
            duplicate_exact_rejections += 1

    overflow_found = False
    for size in range(2, min(4, len(selectors)) + 1):
        if overflow_found:
            break
        for selected_records in combinations(selectors, size):
            if sum(len(record["selectable_layer3"]) for record in selected_records) <= 3:
                continue
            evidence = _activation_evidence(selected_records)
            if evidence is None:
                continue
            try:
                layer3_selector_runtime_selection_receipt(
                    projection,
                    evidence_signals=evidence,
                    build_identity=build_identity,
                )
            except ValidationProblem as exc:
                if "more than three Layer 3" in str(exc):
                    over_max_rejections += 1
                    overflow_found = True
                    break
                errors.append(str(exc))

    return (
        sorted(
            classes_by_selected.values(),
            key=lambda item: (len(item["selected_layer3"]), item["selected_layer3"]),
        ),
        {
            "positive_selector_case_count": positive_cases,
            "nearest_negative_case_count": nearest_negative_cases,
            "nearest_negative_leak_count": nearest_negative_leaks,
            "over_max_rejection_count": over_max_rejections,
            "unauthorized_exact_rejection_count": unauthorized_exact_rejections,
            "duplicate_exact_rejection_count": duplicate_exact_rejections,
            "receipt_replay_count": 1 if not replay_errors else 0,
        },
        errors,
    )


def _registry_rows_by_name(document: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    return {
        row["name"]: row
        for row in document[key]
        if isinstance(row, dict) and isinstance(row.get("name"), str)
    }


def _eligible_reference_entries(
    row: dict[str, Any],
    profile: str,
) -> list[dict[str, Any]]:
    return [
        entry
        for entry in row.get("reference_index", [])
        if isinstance(entry, dict)
        and profile in entry.get("required_by", [])
    ]


def _reference_envelopes(
    rows: list[tuple[str, dict[str, Any]]],
    context_authority: dict[str, object],
) -> tuple[list[list[tuple[str, dict[str, Any]]]], int, int, int, int]:
    """Return maximal legal selected unions without deciding stage residency.

    A selected union may contain independent Reference decisions.  Only the
    v3 staged planner's reciprocal must-co-trigger components authorize shared
    residency.  This conflict frontier establishes union legality; it never
    preloads a resident set.  Memoized independent-set counting avoids
    enumerating or tokenizing dominated subsets.
    """

    non_index = [
        (owner, entry)
        for owner, entry in rows
        if entry.get("type") != "index"
    ]
    forbidden_indexes = len(rows) - len(non_index)
    conflict_pairs: set[tuple[int, int]] = set()
    for left, right in combinations(range(len(non_index)), 2):
        left_owner, left_entry = non_index[left]
        right_owner, right_entry = non_index[right]
        if left_owner != right_owner:
            continue
        decision = reference_context_admissibility_decisions(
            context_authority,
            references=[
                (left_owner, left_entry["path"]),
                (right_owner, right_entry["path"]),
            ],
            path="analyzed",
        )
        if decision["failure_id"] == "context-reference-conflict":
            conflict_pairs.add((left, right))

    full_mask = (1 << len(non_index)) - 1
    neighbors = [0] * len(non_index)
    for left, right in conflict_pairs:
        neighbors[left] |= 1 << right
        neighbors[right] |= 1 << left

    independent_count_cache: dict[int, int] = {}

    def independent_count(mask: int) -> int:
        cached = independent_count_cache.get(mask)
        if cached is not None:
            return cached
        if not mask:
            return 1
        vertex_bit = mask & -mask
        vertex = vertex_bit.bit_length() - 1
        without_vertex = mask & ~vertex_bit
        count = independent_count(without_vertex) + independent_count(
            without_vertex & ~neighbors[vertex]
        )
        independent_count_cache[mask] = count
        return count

    frontier = {full_mask}
    changed = True
    while changed:
        changed = False
        next_frontier: set[int] = set()
        for mask in frontier:
            conflict = next(
                (
                    (left, right)
                    for left, right in sorted(conflict_pairs)
                    if mask & (1 << left) and mask & (1 << right)
                ),
                None,
            )
            if conflict is None:
                next_frontier.add(mask)
                continue
            changed = True
            left, right = conflict
            next_frontier.add(mask & ~(1 << left))
            next_frontier.add(mask & ~(1 << right))
        frontier = next_frontier
    maximal_masks = sorted(
        (
            mask
            for mask in frontier
            if not any(mask != other and mask & other == mask for other in frontier)
        ),
        key=lambda mask: (
            -mask.bit_count(),
            tuple(
                (non_index[index][0], non_index[index][1]["path"])
                for index in range(len(non_index))
                if mask & (1 << index)
            ),
        ),
    )
    envelopes = [
        [
            non_index[index]
            for index in range(len(non_index))
            if mask & (1 << index)
        ]
        for mask in maximal_masks
    ] or [[]]
    legal_subset_count = independent_count(full_mask)
    return (
        envelopes,
        legal_subset_count - len(envelopes),
        forbidden_indexes,
        len(conflict_pairs),
        legal_subset_count,
    )


def _capsule_envelopes(cases):
    envelopes = {}
    for _, case in cases:
        for index, step in enumerate(case["steps"]):
            if step.get("action") != "dispatch": continue
            rendered = validate_and_render_fixture_capsule(step)
            kind = _budget_class(step, "", [])
            component = _component("dispatch_assignment", f"fixture:{case['id']}:{index}", rendered)
            if kind not in envelopes or component["tokens"] > envelopes[kind]["tokens"]:
                envelopes[kind] = component
    return envelopes


def _component_upper_bound(components: list[dict[str, Any]]) -> int:
    """Return a memoized component-token dominance score without re-tokenizing."""

    return sum(component["tokens"] for component in components) + max(
        0, len(components) - 1
    ) * CONTEXT_COMPONENT_SEPARATOR_TOKENS


def _token_distribution(values: list[int]) -> dict[str, int | None]:
    """Return deterministic nearest-rank distribution statistics."""

    ordered = sorted(values)
    if not ordered:
        return {
            "count": 0,
            "p50": None,
            "p90": None,
            "p95": None,
            "p99": None,
            "max": None,
        }

    def nearest_rank(percentile: int) -> int:
        index = max(0, ((percentile * len(ordered) + 99) // 100) - 1)
        return ordered[index]

    return {
        "count": len(ordered),
        "p50": nearest_rank(50),
        "p90": nearest_rank(90),
        "p95": nearest_rank(95),
        "p99": nearest_rank(99),
        "max": ordered[-1],
    }


def _unavailable_growth_distribution() -> dict[str, Any]:
    return {
        "status": "unavailable",
        "reason": "single-snapshot evaluation has no prior comparable valid-context population",
        "count": 0,
        "p50": None,
        "p90": None,
        "p95": None,
        "p99": None,
        "max": None,
    }


def _main_utility_selection_rows(
    main_contexts: list[dict[str, Any]],
    dispatch_measurements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Project stable measured rows for classes outside the dominance mapping."""

    rows: list[dict[str, Any]] = []
    for measurement in [
        *main_contexts,
        *(
            item
            for item in dispatch_measurements
            if item.get("budget_class") == "utility"
        ),
    ]:
        budget_class = measurement.get("budget_class")
        if budget_class not in {"main", "utility"}:
            raise ValueError(
                "selection identity rows may contain only main or utility measurements"
            )
        components = measurement.get("components")
        if not isinstance(components, list) or not components:
            raise ValueError(
                f"{budget_class} selection identity requires measured components"
            )
        render_signature = [
            {
                key: component[key]
                for key in ("kind", "path", "sha256", "tokens")
            }
            for component in components
        ]
        candidate_identity = {
            "host": measurement.get("host"),
            "runtime": measurement.get("runtime"),
        }
        if budget_class == "utility":
            candidate_identity.update(
                {
                    "step": measurement.get("step"),
                    "role": measurement.get("role"),
                    "mode": measurement.get("mode"),
                    "primary_skill": measurement.get("primary_skill"),
                    "layer3_skills": measurement.get("layer3_skills", []),
                    "layer3_references": measurement.get(
                        "layer3_references", []
                    ),
                    "professional_references": measurement.get(
                        "professional_references", []
                    ),
                    "canonical_capsule_sha256": measurement.get(
                        "canonical_capsule_sha256"
                    ),
                }
            )
        tokens = measurement.get("total_tokens")
        if not isinstance(tokens, int) or isinstance(tokens, bool):
            raise ValueError(
                f"{budget_class} selection identity requires measured integer tokens"
            )
        rows.append(
            {
                "budget_class": budget_class,
                "candidate_identity": candidate_identity,
                "render_signature_sha256": _sha256_text(
                    _canonical_json_text(render_signature)
                ),
                "tokens": tokens,
            }
        )
    return sorted(rows, key=_canonical_json_text)


def _calibration_selection_identity(
    selected_valid_candidate_rows: Any,
    contract: dict[str, Any],
) -> str:
    """Fingerprint canonical measured valid-candidate rows without budget fields."""

    return _sha256_text(
        _canonical_json_text(
            {
                "tokenizer": contract["tokenizer"],
                "valid_candidate_measurements": selected_valid_candidate_rows,
            }
        )
    )


def _render_signature_tokens(candidate: dict[str, Any]) -> int:
    """Measure one exact rendered component signature without duplicate scanning."""

    return count_o200k_base_tokens(
        "\n\n".join(
            component["_text"].rstrip() for component in candidate["components"]
        )
    )


def _active_reference_ids(candidate: dict[str, Any]) -> list[str]:
    """Return source-owned References resident in this measured candidate stage."""

    return sorted(
        f"{owner}/{path}"
        for owner, path in candidate["stage_loaded_references"]
    )


def _frontier_member_witness(
    *,
    member: str,
    tokens: int,
    equivalence_key: tuple[Any, ...],
    render_signature: tuple[tuple[str, str], ...],
) -> dict[str, Any]:
    """Bind one member maximum to compact deterministic candidate evidence."""

    return {
        "member": member,
        "maximum_tokens": tokens,
        "canonical_reduction_key_sha256": _sha256_text(
            _canonical_json_text(equivalence_key)
        ),
        "render_signature_sha256": _sha256_text(
            _canonical_json_text(render_signature)
        ),
    }


def _dominance_frontier_consumer_boundary() -> dict[str, Any]:
    """Prove the eval projection is absent from runtime and build consumers."""

    checked_paths = (
        ROOT / "scripts" / "build.py",
        ROOT / "scripts" / "validation_utils.py",
        ROOT / "src" / "control-prompts" / "main-control-agent.md",
        ROOT
        / "src"
        / "control-skills"
        / "engineering-control-plane"
        / "references"
        / "professional-skill-router.md",
    )
    token = "dominance_frontier"
    runtime_consumers: list[str] = []
    build_consumers: list[str] = []
    checked_fingerprints: dict[str, str] = {}
    for path in checked_paths:
        text = path.read_text(encoding="utf-8")
        relative = _relative(path)
        checked_fingerprints[relative] = _sha256_text(text)
        if token not in text:
            continue
        if path.name == "build.py":
            build_consumers.append(relative)
        else:
            runtime_consumers.append(relative)
    return {
        "projection_only": not runtime_consumers and not build_consumers,
        "runtime_consumers": runtime_consumers,
        "build_consumers": build_consumers,
        "checked_path_fingerprints": checked_fingerprints,
    }


def _dominance_frontier_projection(
    *,
    canonical_candidates: dict[
        str,
        dict[tuple[Any, ...], dict[str, Any]],
    ],
    authority: dict[str, Any],
    control_projections: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Project complete source-derived budget dominance without runtime matching."""

    signature_tokens: dict[tuple[tuple[str, str], ...], int] = {}
    budget_rows: dict[str, dict[str, Any]] = {}
    mapping_hasher = hashlib.sha256()
    component_fingerprints: set[tuple[str, str, str]] = set()

    for budget_class in ADMISSIBLE_BUDGET_CLASSES:
        soft_target = CONTEXT_BUDGET_LIMITS[budget_class]["soft_target"]
        candidates_by_key = canonical_candidates[budget_class]
        signatures: set[tuple[tuple[str, str], ...]] = set()
        candidate_tokens: list[int] = []
        all_members = {
            "professional": set(),
            "layer3": set(),
            "active_reference": set(),
        }
        frontier_members = {
            "professional": set(),
            "layer3": set(),
            "active_reference": set(),
        }
        member_maxima: dict[str, dict[str, tuple[int, str, dict[str, Any]]]] = {
            "professional": {},
            "layer3": {},
            "active_reference": {},
        }
        over_target_candidate_count = 0

        for equivalence_key, candidate in sorted(
            candidates_by_key.items(), key=lambda item: repr(item[0])
        ):
            render_signature = candidate["render_signature"]
            signatures.add(render_signature)
            tokens = signature_tokens.get(render_signature)
            if tokens is None:
                tokens = _render_signature_tokens(candidate)
                signature_tokens[render_signature] = tokens
            candidate_tokens.append(tokens)
            active_references = _active_reference_ids(candidate)
            members = {
                "professional": [candidate["professional_skill"]],
                "layer3": sorted(candidate["selected_layer3"]),
                "active_reference": active_references,
            }
            over_target = tokens > soft_target
            over_target_candidate_count += int(over_target)
            equivalence_key_text = _canonical_json_text(equivalence_key)
            equivalence_key_rank = _sha256_text(equivalence_key_text)
            render_signature_sha256 = _sha256_text(
                _canonical_json_text(render_signature)
            )
            mapping_hasher.update(
                (
                    _canonical_json_text(
                        {
                            "budget_class": budget_class,
                            "canonical_reduction_key": equivalence_key,
                            "render_signature_sha256": render_signature_sha256,
                            "tokens": tokens,
                        }
                    )
                    + "\n"
                ).encode("utf-8")
            )
            component_fingerprints.update(
                (component["kind"], component["path"], component["sha256"])
                for component in candidate["components"]
            )
            for member_kind, values in members.items():
                all_members[member_kind].update(values)
                if over_target:
                    frontier_members[member_kind].update(values)
                for member in values:
                    current = member_maxima[member_kind].get(member)
                    rank = (tokens, equivalence_key_rank)
                    if current is None or rank > (current[0], current[1]):
                        member_maxima[member_kind][member] = (
                            tokens,
                            equivalence_key_rank,
                            _frontier_member_witness(
                                member=member,
                                tokens=tokens,
                                equivalence_key=equivalence_key,
                                render_signature=render_signature,
                            ),
                        )

        outside_members = {
            member_kind: sorted(all_members[member_kind] - frontier_members[member_kind])
            for member_kind in all_members
        }
        budget_rows[budget_class] = {
            "soft_target": soft_target,
            "hard_ceiling": CONTEXT_BUDGET_LIMITS[budget_class]["hard_ceiling"],
            "candidate_count": len(candidates_by_key),
            "exact_render_signature_count": len(signatures),
            "token_distribution": _token_distribution(candidate_tokens),
            "growth_distribution": _unavailable_growth_distribution(),
            "over_target_candidate_count": over_target_candidate_count,
            "frontier_counts": {
                member_kind: len(frontier_members[member_kind])
                for member_kind in frontier_members
            },
            "frontier": {
                member_kind: sorted(frontier_members[member_kind])
                for member_kind in frontier_members
            },
            "frontier_witnesses": {
                member_kind: [
                    member_maxima[member_kind][member][2]
                    for member in sorted(frontier_members[member_kind])
                ]
                for member_kind in frontier_members
            },
            "outside_counts": {
                member_kind: len(outside_members[member_kind])
                for member_kind in outside_members
            },
            "outside": {
                member_kind: [
                    {
                        "member": member,
                        "maximum_tokens": member_maxima[member_kind][member][0],
                    }
                    for member in outside_members[member_kind]
                ]
                for member_kind in outside_members
            },
        }

    task_review_classes = ("task", "review")
    global_all: dict[str, set[str]] = {
        member_kind: set()
        for member_kind in ("professional", "layer3", "active_reference")
    }
    global_frontier: dict[str, set[str]] = {
        member_kind: set() for member_kind in global_all
    }
    for budget_class in task_review_classes:
        row = budget_rows[budget_class]
        for member_kind in global_all:
            global_frontier[member_kind].update(row["frontier"][member_kind])
            global_all[member_kind].update(row["frontier"][member_kind])
            global_all[member_kind].update(
                item["member"] for item in row["outside"][member_kind]
            )
    safe_complement = {
        member_kind: sorted(global_all[member_kind] - global_frontier[member_kind])
        for member_kind in global_all
    }

    component_mapping_text = "\n".join(
        _canonical_json_text(row) for row in sorted(component_fingerprints)
    )
    runtime_manifest_path = (
        DIST_SKILLS / RUNTIME_NAME / ".changeforge-build-manifest.json"
    )
    source_fingerprints = {
        "registries": {
            _relative(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                PROFESSIONAL_REGISTRY,
                FOUNDATION_REGISTRY,
                DOMAIN_REGISTRY,
            )
        },
        "capsule_source": {
            "path": _relative(FIXTURES),
            "sha256": hashlib.sha256(FIXTURES.read_bytes()).hexdigest(),
        },
        "runtime_manifest": {
            "runtime": RUNTIME_NAME,
            "path": _relative(runtime_manifest_path),
            "sha256": hashlib.sha256(runtime_manifest_path.read_bytes()).hexdigest(),
        },
        "selector_authority_sha256": _sha256_text(_canonical_json_text(authority)),
        "control_projection_sha256": _sha256_text(
            _canonical_json_text(control_projections)
        ),
        "render_component_inventory": {
            "count": len(component_fingerprints),
            "mapping_sha256": _sha256_text(component_mapping_text),
        },
    }
    return {
        "contract": "changeforge.context-dominance-frontier/v1",
        "projection_scope": "eval-only canonical admissible compositions",
        "budget_classes": budget_rows,
        "global_task_review_union": {
            "frontier_counts": {
                member_kind: len(global_frontier[member_kind])
                for member_kind in global_frontier
            },
            "frontier": {
                member_kind: sorted(global_frontier[member_kind])
                for member_kind in global_frontier
            },
            "safe_complement_counts": {
                member_kind: len(safe_complement[member_kind])
                for member_kind in safe_complement
            },
            "safe_complement": safe_complement,
        },
        "source_fingerprints": source_fingerprints,
        "mapping_row_count": sum(
            len(candidates) for candidates in canonical_candidates.values()
        ),
        "mapping_digest": mapping_hasher.hexdigest(),
        "consumer_boundary": _dominance_frontier_consumer_boundary(),
        "completeness": {
            "numeric_cap": None,
            "truncation": False,
            "task_matcher": False,
            "index_or_catalog_preload": False,
            "canonical_representatives_exhausted": True,
        },
    }


def _evaluate_admissible_context_compositions(
    *,
    cases: list[tuple[str, dict[str, Any]]],
    runtime_manifests: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Measure source-derived selector/reference composition equivalence classes."""

    errors: list[str] = []
    admissible_digest = runtime_manifests.get(RUNTIME_NAME, {}).get(
        "authoritative_build_inputs", {}
    ).get("sha256")
    if (
        not isinstance(admissible_digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", admissible_digest) is None
    ):
        raise ValueError("admissible context Runtime build identity is missing")
    admissible_build_identity = runtime_asset_build_identity(admissible_digest)
    authority = _selector_authority()
    control_projections = layer3_selector_control_projections(authority)
    professional_document = load_yaml_file(PROFESSIONAL_REGISTRY)
    foundation_document = load_yaml_file(FOUNDATION_REGISTRY)
    domain_document = load_yaml_file(DOMAIN_REGISTRY)
    context_authority = reference_context_admissibility_authority(
        professional_document,
        foundation_document,
        domain_document,
        context="rendered context admissibility",
    )
    professional_rows = _registry_rows_by_name(
        professional_document,
        "professional_skills",
    )
    layer3_rows = {
        **_registry_rows_by_name(foundation_document, "foundation_skills"),
        **_registry_rows_by_name(domain_document, "domain_skills"),
    }
    domain_names = set(authority["runtime_domains"])
    capsule_envelopes = _capsule_envelopes(cases)
    component_cache: dict[tuple[str, Path], dict[str, Any]] = {}

    def file_component(kind: str, path: Path) -> dict[str, Any]:
        key = (kind, path)
        if key not in component_cache:
            component_cache[key] = _file_component(kind, path)
        return component_cache[key]

    profile_variants: dict[str, tuple[str, Path]] = {}
    for profile in ("analysis-agent", "task-agent", "review-agent"):
        profile_variants[profile] = max(
            (
                (host, _profile_path(host, profile))
                for host in HOST_PROFILE_ROOTS
            ),
            key=lambda item: (
                file_component("worker_profile", item[1])["tokens"],
                file_component("worker_profile", item[1])["sha256"],
                item[0],
            ),
        )

    inventory = {
        "professional_count": len(control_projections),
        "owner_surface_count": 0,
        "legal_selection_equivalence_class_count": 0,
        "positive_selector_case_count": 0,
        "nearest_negative_case_count": 0,
        "professional_reference_count": 0,
        "professional_reference_conflict_count": 0,
        "nested_reference_count": 0,
        "legal_nested_reference_combination_count": 0,
        "dominated_reference_subset_count": 0,
        "maximum_loaded_reference_count": 0,
        "maximum_selected_reference_count": 0,
        "four_plus_reference_measurement_count": 0,
        "stage_measurement_count": 0,
        "valid_carried_predecessor_count": 0,
        "required_output_receipt_count": 0,
        "required_output_receipt_failure_count": 0,
        "carrier_failure_count": 0,
        "dropped_reference_obligation_count": 0,
        "path_excluded_composition_count": 0,
        "path_exclusions": {},
        "layer3_cardinality_counts": {str(value): 0 for value in range(4)},
        "candidate_composition_count": 0,
        "canonical_representative_count": 0,
        "coverage_mapping_count": 0,
        "exact_measurement_count": 0,
        "upper_bound_dominated_count": 0,
        "host_variant_dominated_count": 0,
    }
    forbidden = {
        "maximum_layer3": 3,
        "overflow_failure_id": "admissible-context-layer3-overflow",
        "over_max_rejection_count": 0,
        "unauthorized_exact_rejection_count": 0,
        "duplicate_exact_rejection_count": 0,
        "nearest_negative_leak_count": 0,
        "index_or_catalog_load_count": 0,
        "index_reference_forbidden_count": 0,
        "silent_truncation_count": 0,
        "reference_conflict_leak_count": 0,
    }
    required_coverage = {
        "analysis_foundation_domain": False,
        "analyzed_task_three_layer3": False,
        "review_domain_foundation": False,
        "nested_targeted_references": False,
        "direct_main_owner": False,
        "initial_analysis_main_owner": False,
        "analyzed_brief_owner": False,
    }
    professional_reference_ids: set[tuple[str, str, str]] = set()
    nested_reference_ids: set[tuple[str, str, str]] = set()
    maxima: dict[str, dict[str, Any] | None] = {
        budget_class: None for budget_class in ADMISSIBLE_BUDGET_CLASSES
    }
    canonical_candidates: dict[
        str,
        dict[tuple[Any, ...], dict[str, Any]],
    ] = {budget_class: {} for budget_class in ADMISSIBLE_BUDGET_CLASSES}
    receipt_replay_count = 0
    surface_count = 0

    for projection_document in control_projections.values():
        professional = projection_document["professional_skill"]
        professional_row = professional_rows[professional]
        for projection in projection_document["selection_surfaces"]:
            surface_count += 1
            profile = projection["profile"]
            owner = projection["selection_owner"]
            if profile == "analysis-agent" and owner == "main-control-agent":
                required_coverage["initial_analysis_main_owner"] = True
            if profile == "task-agent" and owner == "main-control-agent":
                required_coverage["direct_main_owner"] = True
            if owner == "engineering-brief":
                required_coverage["analyzed_brief_owner"] = True
            classes, selector_stats, selector_errors = (
                _admissible_selector_equivalence_classes(
                    authority,
                    projection,
                    admissible_build_identity,
                )
            )
            errors.extend(selector_errors)
            inventory["legal_selection_equivalence_class_count"] += len(classes)
            for key in (
                "positive_selector_case_count",
                "nearest_negative_case_count",
            ):
                inventory[key] += selector_stats[key]
            for key in (
                "over_max_rejection_count",
                "unauthorized_exact_rejection_count",
                "duplicate_exact_rejection_count",
                "nearest_negative_leak_count",
            ):
                forbidden[key] += selector_stats[key]
            receipt_replay_count += selector_stats["receipt_replay_count"]

            (
                professional_envelopes,
                professional_dominated,
                forbidden_indexes,
                professional_conflicts,
                professional_subset_count,
            ) = _reference_envelopes(
                [
                    (professional, entry)
                    for entry in _eligible_reference_entries(
                        professional_row,
                        profile,
                    )
                ],
                context_authority,
            )
            forbidden["index_reference_forbidden_count"] += forbidden_indexes
            inventory["professional_reference_conflict_count"] += (
                professional_conflicts
            )
            for envelope in professional_envelopes:
                decision = reference_context_admissibility_decisions(
                    context_authority,
                    references=[
                        (reference_owner, entry["path"])
                        for reference_owner, entry in envelope
                    ],
                    path="analyzed",
                )
                if decision["failure_id"] == "context-reference-conflict":
                    forbidden["reference_conflict_leak_count"] += 1
            for envelope in professional_envelopes:
                for reference_owner, entry in envelope:
                    professional_reference_ids.add(
                        (reference_owner, profile, entry["path"])
                    )
            inventory["dominated_reference_subset_count"] += (
                professional_subset_count - len(professional_envelopes)
            )

            if profile == "analysis-agent":
                budget_class = "analysis"
            elif profile == "review-agent":
                budget_class = "review"
            elif owner == "engineering-brief":
                budget_class = "analyzed_task"
            else:
                budget_class = "task"
            capsule = capsule_envelopes.get(budget_class)
            if capsule is None:
                errors.append(
                    f"admissible composition lacks {budget_class} Capsule envelope"
                )
                continue

            for selected_class in classes:
                selected = selected_class["selected_layer3"]
                inventory["layer3_cardinality_counts"][str(len(selected))] += 1
                foundations = [item for item in selected if item not in domain_names]
                domains = [item for item in selected if item in domain_names]
                if profile == "analysis-agent" and foundations and domains:
                    required_coverage["analysis_foundation_domain"] = True
                if (
                    profile == "task-agent"
                    and owner == "engineering-brief"
                    and len(selected) == 3
                ):
                    required_coverage["analyzed_task_three_layer3"] = True
                if profile == "review-agent" and foundations and domains:
                    required_coverage["review_domain_foundation"] = True

                nested_entries: list[tuple[str, dict[str, Any]]] = []
                for layer3_name in selected:
                    row = layer3_rows[layer3_name]
                    for entry in _eligible_reference_entries(row, profile):
                        if entry.get("type") == "index":
                            forbidden["index_reference_forbidden_count"] += 1
                            continue
                        nested_entries.append((layer3_name, entry))
                        nested_reference_ids.add(
                            (layer3_name, profile, entry["path"])
                        )
                        if entry.get("type") == "targeted":
                            required_coverage["nested_targeted_references"] = True
                (
                    nested_envelopes,
                    nested_dominated,
                    nested_forbidden_indexes,
                    nested_conflicts,
                    nested_subset_count,
                ) = _reference_envelopes(nested_entries, context_authority)
                forbidden["index_reference_forbidden_count"] += (
                    nested_forbidden_indexes
                )
                inventory["legal_nested_reference_combination_count"] += (
                    nested_subset_count
                )
                inventory["dominated_reference_subset_count"] += (
                    nested_dominated
                )
                inventory["professional_reference_conflict_count"] += (
                    nested_conflicts
                )

                for runtime_name, manifest in runtime_manifests.items():
                    primary_path = (
                        DIST_SKILLS / runtime_name / professional / "SKILL.md"
                    )
                    if not primary_path.is_file():
                        errors.append(
                            f"missing admissible Professional {_relative(primary_path)}"
                        )
                        continue
                    layer3_components: list[dict[str, Any]] = []
                    failed = False
                    for layer3_name in selected:
                        try:
                            layer3_path = _layer3_path(
                                runtime_name,
                                professional,
                                layer3_name,
                                manifest,
                            )
                        except ValueError as exc:
                            errors.append(str(exc))
                            failed = True
                            break
                        layer3_components.append(
                            file_component("layer3", layer3_path)
                        )
                    if failed:
                        continue
                    nested_component_rows: dict[
                        tuple[str, str], tuple[str, dict[str, Any]]
                    ] = {}
                    for layer3_name, entry in nested_entries:
                        logical_id = f"{layer3_name}/{entry['path']}"
                        try:
                            _runtime_path, nested_path = (
                                _runtime_reference_target_for_authoring_entry(
                                runtime_name,
                                professional,
                                layer3_name,
                                entry,
                                )
                            )
                        except ValueError as exc:
                            errors.append(str(exc))
                            failed = True
                            break
                        if nested_path.name in {"index.md", "catalog.md"}:
                            forbidden["index_or_catalog_load_count"] += 1
                        nested_component_rows[(layer3_name, entry["path"])] = (
                            logical_id,
                            file_component("layer3_reference", nested_path),
                        )
                    if failed:
                        continue
                    nested_component_envelopes = [
                        [
                            nested_component_rows[(reference_owner, entry["path"])]
                            for reference_owner, entry in envelope
                        ]
                        for envelope in nested_envelopes
                    ]

                    for host in (profile_variants[profile][0],):
                        profile_path = profile_variants[profile][1]
                        for professional_envelope in professional_envelopes:
                            for nested_envelope, nested_source_envelope in zip(
                                nested_component_envelopes,
                                nested_envelopes,
                                strict=True,
                            ):
                                selected_references = [
                                    (reference_owner, entry["path"])
                                    for reference_owner, entry in professional_envelope
                                ] + [
                                    (reference_owner, entry["path"])
                                    for reference_owner, entry in nested_source_envelope
                                ]
                                composition_path = (
                                    "direct"
                                    if budget_class == "task"
                                    or (
                                        budget_class == "review"
                                        and owner == "main-control-agent"
                                    )
                                    else "analyzed"
                                )
                                reachability = (
                                    reference_context_admissibility_decisions(
                                        context_authority,
                                        references=selected_references,
                                        path=composition_path,
                                    )
                                )
                                if not reachability["reachable"]:
                                    inventory["path_excluded_composition_count"] += 1
                                    failure_id = reachability["failure_id"]
                                    path_exclusions = inventory["path_exclusions"]
                                    path_exclusions[failure_id] = (
                                        path_exclusions.get(failure_id, 0) + 1
                                    )
                                    if (
                                        composition_path == "direct"
                                        and professional == "backend-change-builder"
                                        and {
                                            "domain-object-identification",
                                            "filesystem-process-safety",
                                        }
                                        <= set(selected)
                                    ):
                                        required_coverage[
                                            "direct_false_worst_excluded"
                                        ] = True
                                    continue
                                carrier_fields = (
                                    context_authority["carrier_fields"][profile][
                                        "engineering-brief"
                                    ]
                                    if profile in {"task-agent", "review-agent"}
                                    and owner == "engineering-brief"
                                    else []
                                )
                                staged_plan = reference_context_staged_plan(
                                    context_authority,
                                    references=selected_references,
                                    path=composition_path,
                                    profile=profile,
                                    selection_owner=owner,
                                    available_carrier_fields=carrier_fields,
                                    receipt_replayed=True,
                                    brief_current=owner == "engineering-brief",
                                    review_fresh=(
                                        profile != "review-agent"
                                        or owner == "engineering-brief"
                                    ),
                                )
                                if not staged_plan["reachable"]:
                                    inventory["carrier_failure_count"] += 1
                                    errors.append(
                                        "admissible composition rejected a current "
                                        f"carrier for {professional}:{profile}:{owner}: "
                                        f"{staged_plan['failure_id']}"
                                    )
                                    continue
                                selected_union = {
                                    tuple(reference)
                                    for reference in staged_plan["selected_union"]
                                }
                                loaded_union = {
                                    tuple(reference)
                                    for reference in staged_plan["loaded_union"]
                                }
                                carried_union = {
                                    tuple(reference)
                                    for reference in staged_plan[
                                        "carried_predecessors"
                                    ]
                                }
                                receipt_rows = staged_plan[
                                    "required_output_receipts"
                                ]
                                receipt_union = {
                                    tuple(receipt["reference"])
                                    for receipt in receipt_rows
                                }
                                receipts_complete = all(
                                    isinstance(receipt.get("required_outputs"), list)
                                    and bool(receipt["required_outputs"])
                                    for receipt in receipt_rows
                                )
                                if selected_union != loaded_union:
                                    inventory[
                                        "dropped_reference_obligation_count"
                                    ] += 1
                                    errors.append(
                                        "admissible staged composition dropped a "
                                        f"Reference obligation for {professional}:"
                                        f"{profile}:{owner}"
                                    )
                                    continue
                                if (
                                    receipt_union != selected_union
                                    or not receipts_complete
                                ):
                                    inventory[
                                        "required_output_receipt_failure_count"
                                    ] += 1
                                    errors.append(
                                        "admissible staged composition dropped a "
                                        f"required-output receipt for {professional}:"
                                        f"{profile}:{owner}"
                                    )
                                    continue
                                inventory["maximum_selected_reference_count"] = max(
                                    inventory["maximum_selected_reference_count"],
                                    len(selected_union),
                                )
                                inventory["valid_carried_predecessor_count"] += len(
                                    carried_union
                                )
                                inventory["required_output_receipt_count"] += len(
                                    receipt_rows
                                )

                                professional_component_rows: dict[
                                    tuple[str, str], dict[str, Any]
                                ] = {}
                                reference_failed = False
                                for reference_owner, entry in professional_envelope:
                                    try:
                                        _runtime_path, reference_path = (
                                            _runtime_reference_target_for_authoring_entry(
                                            runtime_name,
                                            professional,
                                            reference_owner,
                                            entry,
                                            )
                                        )
                                    except ValueError as exc:
                                        errors.append(str(exc))
                                        reference_failed = True
                                        break
                                    professional_component_rows[
                                        (reference_owner, entry["path"])
                                    ] = file_component(
                                        "targeted_reference",
                                        reference_path,
                                    )
                                if reference_failed:
                                    continue
                                for stage in staged_plan["stages"]:
                                    loaded_references = {
                                        tuple(reference)
                                        for reference in stage["loaded_references"]
                                    }
                                    carried_predecessors = {
                                        tuple(reference)
                                        for reference in stage[
                                            "carried_predecessors"
                                        ]
                                    }
                                    components = [
                                        file_component(
                                            "worker_profile",
                                            profile_path,
                                        ),
                                        file_component("primary_skill", primary_path),
                                    ]
                                    loaded_paths: list[str] = [
                                        _relative(profile_path),
                                        _relative(primary_path),
                                    ]
                                    for reference, component in (
                                        professional_component_rows.items()
                                    ):
                                        if reference not in loaded_references:
                                            continue
                                        components.append(component)
                                        loaded_paths.append(component["path"])
                                    components.extend(layer3_components)
                                    loaded_paths.extend(
                                        item["path"] for item in layer3_components
                                    )
                                    loaded_nested_logical_ids: list[str] = []
                                    for reference, (
                                        logical_id,
                                        component,
                                    ) in nested_component_rows.items():
                                        if reference not in loaded_references:
                                            continue
                                        components.append(component)
                                        loaded_paths.append(component["path"])
                                        loaded_nested_logical_ids.append(logical_id)
                                    components.append(capsule)
                                    loaded_paths.append(capsule["path"])
                                    inventory["candidate_composition_count"] += len(
                                        HOST_PROFILE_ROOTS
                                    )
                                    inventory["host_variant_dominated_count"] += (
                                        len(HOST_PROFILE_ROOTS) - 1
                                    )
                                    inventory["stage_measurement_count"] += 1
                                    component_score = sum(
                                        component["tokens"]
                                        for component in components
                                    )
                                    equivalence_key = (
                                        professional,
                                        profile,
                                        owner,
                                        len(selected),
                                        len(foundations),
                                        len(domains),
                                        tuple(sorted(selected_union)),
                                        stage["stage"],
                                        tuple(sorted(loaded_references)),
                                        tuple(sorted(carried_predecessors)),
                                    )
                                    render_signature = tuple(
                                        (component["kind"], component["sha256"])
                                        for component in components
                                    )
                                    candidate = {
                                        "component_score": component_score,
                                        "component_upper_bound": _component_upper_bound(
                                            components
                                        ),
                                        "render_signature": render_signature,
                                        "host": host,
                                        "runtime": runtime_name,
                                        "profile": profile,
                                        "selection_owner": owner,
                                        "professional_skill": professional,
                                        "selected_layer3": list(selected),
                                        "selected_layer3_references": sorted(
                                            loaded_nested_logical_ids
                                        ),
                                        "selected_reference_union": [
                                            list(reference)
                                            for reference in sorted(selected_union)
                                        ],
                                        "loaded_reference_union": [
                                            list(reference)
                                            for reference in sorted(loaded_union)
                                        ],
                                        "stage": stage["stage"],
                                        "stage_loaded_references": [
                                            list(reference)
                                            for reference in sorted(
                                                loaded_references
                                            )
                                        ],
                                        "stage_carried_predecessors": [
                                            list(reference)
                                            for reference in sorted(
                                                carried_predecessors
                                            )
                                        ],
                                        "stage_required_output_receipts": stage[
                                            "required_output_receipts"
                                        ],
                                        "carrier_validated": staged_plan[
                                            "carrier_validated"
                                        ],
                                        "foundation": foundations,
                                        "domain": domains,
                                        "loaded_paths": loaded_paths,
                                        "components": components,
                                    }
                                    loaded_reference_count = len(loaded_references)
                                    inventory[
                                        "maximum_loaded_reference_count"
                                    ] = max(
                                        inventory[
                                            "maximum_loaded_reference_count"
                                        ],
                                        loaded_reference_count,
                                    )
                                    if loaded_reference_count >= 4:
                                        inventory[
                                            "four_plus_reference_measurement_count"
                                        ] += 1
                                    current = canonical_candidates[
                                        budget_class
                                    ].get(equivalence_key)
                                    candidate_rank = (
                                        component_score,
                                        candidate["component_upper_bound"],
                                        render_signature,
                                    )
                                    current_rank = (
                                        (
                                            current["component_score"],
                                            current["component_upper_bound"],
                                            current["render_signature"],
                                        )
                                        if current is not None
                                        else None
                                    )
                                    if (
                                        current_rank is None
                                        or candidate_rank > current_rank
                                    ):
                                        canonical_candidates[budget_class][
                                            equivalence_key
                                        ] = candidate
                                    inventory[
                                        "upper_bound_dominated_count"
                                    ] += int(current is not None)

    dominance_frontier = _dominance_frontier_projection(
        canonical_candidates=canonical_candidates,
        authority=authority,
        control_projections=control_projections,
    )
    consumer_boundary = dominance_frontier["consumer_boundary"]
    if not consumer_boundary["projection_only"]:
        errors.append(
            "dominance frontier must remain eval-only; runtime/build consumer found"
        )
    exact_measurement_cache: dict[
        tuple[str, tuple[tuple[str, str], ...]],
        dict[str, Any],
    ] = {}
    for budget_class, candidates_by_class in canonical_candidates.items():
        for equivalence_key, candidate in sorted(
            candidates_by_class.items(),
            key=lambda item: (
                -item[1]["component_upper_bound"],
                repr(item[0]),
            ),
        ):
            maximum = maxima[budget_class]
            if (
                maximum is not None
                and candidate["component_upper_bound"] <= maximum["tokens"]
            ):
                inventory["upper_bound_dominated_count"] += 1
                continue
            cache_key = (budget_class, candidate["render_signature"])
            measurement = exact_measurement_cache.get(cache_key)
            if measurement is None:
                measurement = _measure_context(
                    candidate["components"],
                    budget_class=budget_class,
                )
                exact_measurement_cache[cache_key] = measurement
                inventory["exact_measurement_count"] += 1
            result = {
                "tokens": measurement["total_tokens"],
                "sum_component_tokens": measurement["sum_component_tokens"],
                "component_upper_bound_tokens": candidate[
                    "component_upper_bound"
                ],
                "soft_target": measurement["soft_target"],
                "hard_ceiling": measurement["hard_ceiling"],
                "within_soft_target": measurement["within_soft_target"],
                "within_hard_ceiling": measurement["within_hard_ceiling"],
                "soft_margin_tokens": measurement["soft_margin_tokens"],
                "hard_margin_tokens": measurement["hard_margin_tokens"],
                "budget_signal": measurement["budget_signal"],
                "within_duplicate_budget": measurement[
                    "within_duplicate_budget"
                ],
                "route_obligations_preserved": True,
                "host": candidate["host"],
                "runtime": candidate["runtime"],
                "profile": candidate["profile"],
                "selection_owner": candidate["selection_owner"],
                "professional_skill": candidate["professional_skill"],
                "selected_layer3": candidate["selected_layer3"],
                "selected_layer3_references": candidate[
                    "selected_layer3_references"
                ],
                "selected_reference_union": candidate[
                    "selected_reference_union"
                ],
                "loaded_reference_union": candidate[
                    "loaded_reference_union"
                ],
                "stage": candidate["stage"],
                "stage_loaded_references": candidate[
                    "stage_loaded_references"
                ],
                "stage_carried_predecessors": candidate[
                    "stage_carried_predecessors"
                ],
                "stage_required_output_receipts": candidate[
                    "stage_required_output_receipts"
                ],
                "carrier_validated": candidate["carrier_validated"],
                "foundation": candidate["foundation"],
                "domain": candidate["domain"],
                "loaded_paths": candidate["loaded_paths"],
                "canonical_reduction_key": [
                    str(value) for value in equivalence_key
                ],
            }
            if maximum is None or result["tokens"] > maximum["tokens"]:
                maxima[budget_class] = result

    inventory["owner_surface_count"] = surface_count
    inventory["canonical_representative_count"] = sum(
        len(candidates) for candidates in canonical_candidates.values()
    )
    inventory["coverage_mapping_count"] = inventory[
        "candidate_composition_count"
    ]
    inventory["professional_reference_count"] = len(professional_reference_ids)
    inventory["nested_reference_count"] = len(nested_reference_ids)
    for name, covered in required_coverage.items():
        if not covered:
            errors.append(f"admissible composition coverage missing {name}")
    if forbidden["nearest_negative_leak_count"]:
        errors.append("admissible composition nearest-negative selection leaked")
    if forbidden["index_or_catalog_load_count"]:
        errors.append("admissible composition loaded an index or catalog")
    if forbidden["reference_conflict_leak_count"]:
        errors.append("admissible composition loaded conflicting References")
    if forbidden["over_max_rejection_count"] == 0:
        errors.append("admissible composition did not prove >3 fail-closed")
    for budget_class in ADMISSIBLE_BUDGET_CLASSES:
        maximum = maxima[budget_class]
        if maximum is None:
            errors.append(f"admissible composition lacks {budget_class} measurement")
            continue
        if not maximum["within_duplicate_budget"]:
            errors.append(
                f"admissible composition {budget_class} duplicate budget failed"
            )

    return {
        "contract": ADMISSIBLE_COMPOSITION_CONTRACT,
        "parallel_catalog": False,
        "source_scope": {
            "registries": [
                _relative(PROFESSIONAL_REGISTRY),
                _relative(FOUNDATION_REGISTRY),
                _relative(DOMAIN_REGISTRY),
            ],
            "selector_authority": (
                "scripts/validation_utils.py::layer3_selector_authority"
            ),
            "selector_consumer": (
                "scripts/validation_utils.py::"
                "layer3_selector_runtime_selection_receipt"
            ),
            "build_projection": "dist/*/.changeforge-build-manifest.json",
            "capsule_source": _relative(FIXTURES),
            "reference_reduction": (
                "every registry role-compatible non-index subset maps to a "
                "maximal legal selected union; independent References remain "
                "singleton resident stages and only reciprocal must-co-trigger "
                "components share residency"
            ),
            "canonical_reduction": (
                "professional/profile/owner, Layer 3 cardinality, "
                "Foundation/Domain shape, Professional Reference envelope, and "
                "nested Reference shape; each stratum retains the highest "
                "source-component token score"
            ),
        },
        "selector_authority_inventory": authority["inventory"],
        "inventory": inventory,
        "required_coverage": required_coverage,
        "max_by_budget_class": maxima,
        "dominance_frontier": dominance_frontier,
        "obligation_preservation": {
            "professional_preserved": all(
                maximum is not None and bool(maximum["professional_skill"])
                for maximum in maxima.values()
            ),
            "domain_authorization_preserved": all(
                maximum is not None
                and set(maximum["domain"])
                <= set(
                    authority["runtime_professionals"][
                        maximum["professional_skill"]
                    ]["domain_authorization"]
                )
                for maximum in maxima.values()
            ),
            "review_selection_independent": all(
                surface["selection_basis"] == "review-risk"
                for document in control_projections.values()
                for surface in document["selection_surfaces"]
                if surface["profile"] == "review-agent"
            ),
            "receipts_replayed": receipt_replay_count == surface_count,
            "route_once_input_only": True,
            "routing_classification_calls": 0,
            "staged_reference_obligations_preserved": (
                inventory["dropped_reference_obligation_count"] == 0
                and inventory["required_output_receipt_failure_count"] == 0
                and inventory["carrier_failure_count"] == 0
            ),
        },
        "forbidden_combinations": forbidden,
        "proof_limits": [
            "Selector equivalence classes use declarative positive and nearest-negative signals; the evaluator does not classify task prose.",
            "Reference subset coverage is a conservative role-compatible upper envelope; registry indexes and catalogs are forbidden and mode contracts remain isolated.",
            "Capsule contribution uses the largest validated checked-in fixture Capsule per budget class, not arbitrary future user prose.",
            "Every legal render candidate maps to one source-derived reduction stratum; exact tokenization is memoized by ordered component fingerprint and applied to the highest component-token representative of every stratum.",
            "Sequenced Reference stages are source-owned; only canonically replayed engineering-brief Task/Review carriers may replace a predecessor body, while other owner surfaces conservatively co-load.",
            "Reported maxima are exact for the deterministic canonical representatives; the full inventory count and dominance mapping remain available separately.",
        ],
        "errors": errors,
    }


def _budget_governance_report(
    *,
    mode: str,
    main_contexts: list[dict[str, Any]],
    dispatch_measurements: list[dict[str, Any]],
    admissible_context_compositions: dict[str, Any],
) -> dict[str, Any]:
    if mode not in {"calibration", "conformance"}:
        raise ValueError("rendered context mode must be calibration or conformance")

    populations: dict[str, dict[str, int | None]] = {
        "main": _token_distribution(
            [measurement["total_tokens"] for measurement in main_contexts]
        ),
        "utility": _token_distribution(
            [
                measurement["total_tokens"]
                for measurement in dispatch_measurements
                if measurement["budget_class"] == "utility"
            ]
        ),
    }
    dominance_rows = admissible_context_compositions["dominance_frontier"][
        "budget_classes"
    ]
    for budget_class in ADMISSIBLE_BUDGET_CLASSES:
        populations[budget_class] = dominance_rows[budget_class][
            "token_distribution"
        ]

    maxima: dict[str, dict[str, Any] | None] = {
        "main": max(
            main_contexts,
            key=lambda measurement: measurement["total_tokens"],
            default=None,
        ),
        "utility": max(
            (
                measurement
                for measurement in dispatch_measurements
                if measurement["budget_class"] == "utility"
            ),
            key=lambda measurement: measurement["total_tokens"],
            default=None,
        ),
        **admissible_context_compositions["max_by_budget_class"],
    }
    advisories: list[dict[str, Any]] = []
    hard_overages: list[dict[str, Any]] = []
    for budget_class in CONTEXT_BUDGET_LIMITS:
        maximum = maxima.get(budget_class)
        if maximum is None:
            continue
        tokens = maximum.get("total_tokens", maximum.get("tokens"))
        if not isinstance(tokens, int):
            continue
        limit = CONTEXT_BUDGET_LIMITS[budget_class]
        if tokens > limit["soft_target"]:
            advisories.append(
                {
                    "budget_class": budget_class,
                    "tokens": tokens,
                    "soft_target": limit["soft_target"],
                    "overage_tokens": tokens - limit["soft_target"],
                }
            )
        if tokens > limit["hard_ceiling"]:
            hard_overages.append(
                {
                    "budget_class": budget_class,
                    "tokens": tokens,
                    "hard_ceiling": limit["hard_ceiling"],
                    "overage_tokens": tokens - limit["hard_ceiling"],
                }
            )

    distributions = {
        budget_class: populations[budget_class]
        for budget_class in CONTEXT_BUDGET_LIMITS
    }
    dominance_frontier = admissible_context_compositions["dominance_frontier"]
    main_utility_rows = _main_utility_selection_rows(
        main_contexts,
        dispatch_measurements,
    )
    population_identity = {
        "admissible_composition_candidates": {
            "budget_classes": list(ADMISSIBLE_BUDGET_CLASSES),
            "mapping_row_count": dominance_frontier["mapping_row_count"],
            "mapping_digest": dominance_frontier["mapping_digest"],
        },
        "main_and_utility_candidates": main_utility_rows,
    }
    selection_count = sum(
        int(distribution["count"] or 0) for distribution in distributions.values()
    )
    bound_selection_count = (
        dominance_frontier["mapping_row_count"] + len(main_utility_rows)
    )
    if bound_selection_count != selection_count:
        raise ValueError(
            "selection identity coverage does not match measured valid-candidate count: "
            f"bound={bound_selection_count}, measured={selection_count}"
        )
    return {
        "mode": mode,
        "source": "src/control-model/core-contracts.json#/context_budget_contract",
        "policy_status": CONTEXT_BUDGET_MODEL["policy_status"],
        "soft_targets": {
            key: value["soft_target"]
            for key, value in CONTEXT_BUDGET_LIMITS.items()
        },
        "hard_ceilings": {
            key: value["hard_ceiling"]
            for key, value in CONTEXT_BUDGET_LIMITS.items()
        },
        "selection_contract": {
            "otherwise_valid_candidates_only": True,
            "budget_applied_to_candidate_selection": False,
            "budget_applied_to_frontier": False,
            "soft_target_applied_to_exit": False,
            "hard_ceiling_applied_to_exit": mode == "conformance",
            "selection_count": selection_count,
            "selection_identity_sha256": _calibration_selection_identity(
                population_identity,
                CONTEXT_BUDGET_MODEL,
            ),
            "identity_excludes_budget_fields": ["soft_target", "hard_ceiling"],
        },
        "distributions": distributions,
        "growth_distributions": {
            budget_class: _unavailable_growth_distribution()
            for budget_class in CONTEXT_BUDGET_LIMITS
        },
        "growth_advisories": advisories,
        "hard_ceiling_overages": hard_overages,
        "conformance_failures": hard_overages if mode == "conformance" else [],
        "duplicate_rule_token_ratio_max": DUPLICATE_TOKEN_RATIO_MAX,
    }


def evaluate(mode: str = "conformance") -> dict[str, Any]:
    errors: list[str] = []
    try:
        document = json.loads(FIXTURES.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read trajectory fixture {FIXTURES}: {exc}") from exc
    if not isinstance(document, dict):
        raise ValueError("trajectory fixture root must be a mapping")
    if document.get("schema_version") != FIXTURE_SCHEMA_VERSION:
        raise ValueError(
            f"trajectory fixture schema_version must be {FIXTURE_SCHEMA_VERSION}"
        )
    cases = _fixture_cases(document)
    expected_case_ids = {str(case.get("id") or "") for _group, case in cases}
    lightweight = json.loads(LIGHTWEIGHT_REPORT.read_text())
    if lightweight.get("status") != "pass" or lightweight.get("errors") != [] or {
        row["id"] for row in lightweight.get("cases", [])
    } != expected_case_ids:
        raise ValueError("current passing lightweight cases are required")
    runtime_manifest = _load_runtime_manifest(errors)
    if runtime_manifest is None:
        raise ValueError("the Runtime build manifest is required")

    prompt_tokens = count_o200k_base_tokens(CONTROL_PROMPT.read_text(encoding="utf-8"))
    main_contexts: list[dict[str, Any]] = []
    for host in HOST_PROFILE_ROOTS:
        profile_path = _profile_path(host, "main-control-agent")
        if not profile_path.is_file():
            errors.append(f"missing rendered Profile {_relative(profile_path)}")
            continue
        for runtime_name in (RUNTIME_NAME,):
            _validate_profile_digest(
                host,
                "main-control-agent",
                profile_path,
                runtime_manifest,
                errors,
            )
            control_skill = DIST_SKILLS / runtime_name / "engineering-control-plane" / "SKILL.md"
            if not control_skill.is_file():
                errors.append(f"missing built Control Skill {_relative(control_skill)}")
                continue
            measurement = _measure_context(
                [
                    _file_component("rendered_main_profile", profile_path),
                    _file_component("control_skill", control_skill),
                ],
                budget_class="main",
            )
            measurement.update(
                {
                    "host": host,
                    "runtime": runtime_name,
                    "embedded_control_prompt_tokens": prompt_tokens,
                    "control_prompt_accounting": (
                        "included in rendered_main_profile and not added as a separate component"
                    ),
                }
            )
            if not measurement["within_duplicate_budget"]:
                errors.append(
                    f"main:{host}:{runtime_name} duplicate ratio "
                    f"{measurement['duplicate_rule_token_ratio']:.3f} exceeds "
                    f"{DUPLICATE_TOKEN_RATIO_MAX:.2f}"
                )
            main_contexts.append(measurement)

    case_results: list[dict[str, Any]] = []
    dispatch_count = 0
    measurement_count = 0
    for fixture_group, case in cases:
        case_id = str(case.get("id") or "")
        if not case_id:
            errors.append(f"{fixture_group} fixture has no id")
            continue
        steps = case.get("steps")
        if not isinstance(steps, list):
            errors.append(f"{case_id}: steps must be a list")
            continue
        dispatch_results: list[dict[str, Any]] = []
        for index, raw_step in enumerate(steps):
            if not isinstance(raw_step, dict) or raw_step.get("action") != "dispatch":
                continue
            dispatch_count += 1
            step_errors = _dispatch_metadata_errors(
                case_id, index, raw_step, steps
            )
            step_errors.extend(
                _layer3_reference_registry_errors(
                    case_id, index, raw_step
                )
            )
            errors.extend(step_errors)
            if step_errors:
                continue
            canonical_capsule = validate_and_render_fixture_capsule(raw_step)
            role = str(raw_step.get("profile"))
            primary = str(raw_step.get("primary_skill") or "")
            layer3 = raw_step.get("layer3_skills", [])
            if not isinstance(layer3, list):
                errors.append(f"{case_id}: dispatch step {index} layer3_skills must be a list")
                continue
            layer3_references = raw_step.get("layer3_references")
            if "utility_capsule" in raw_step:
                layer3_references = []
            elif not isinstance(layer3_references, list):
                errors.append(
                    f"{case_id}: dispatch step {index} layer3_references must be a list"
                )
                continue
            references = raw_step["professional_references"]
            budget_class = _budget_class(
                raw_step,
                str(case.get("kind") or ""),
                steps,
            )
            for host in HOST_PROFILE_ROOTS:
                profile_path = _profile_path(host, role)
                if not profile_path.is_file():
                    errors.append(f"missing rendered Profile {_relative(profile_path)}")
                    continue
                for runtime_name in (RUNTIME_NAME,):
                    _validate_profile_digest(
                        host,
                        role,
                        profile_path,
                        runtime_manifest,
                        errors,
                    )
                    components = [_file_component("worker_profile", profile_path)]
                    manifest = runtime_manifest
                    if primary:
                        primary_path = DIST_SKILLS / runtime_name / primary / "SKILL.md"
                        if not primary_path.is_file():
                            errors.append(f"missing primary Skill {_relative(primary_path)}")
                            continue
                        components.append(_file_component("primary_skill", primary_path))
                        reference_failed = False
                        for reference in references:
                            try:
                                _record, reference_path = (
                                    _runtime_reference_record_and_target(
                                        DIST_SKILLS / runtime_name / primary,
                                        primary,
                                        reference,
                                    )
                                )
                            except ValueError as exc:
                                errors.append(f"{case_id}: dispatch step {index}: {exc}")
                                reference_failed = True
                                break
                            if not reference_path.is_file():
                                errors.append(
                                    f"{case_id}: dispatch step {index} missing reference "
                                    f"{_relative(reference_path)}"
                                )
                                reference_failed = True
                                break
                            reference_kind = (
                                "mode_reference"
                                if primary == "engineering-change-analysis"
                                and reference == MODE_REFERENCES.get(raw_step.get("mode"))
                                else "targeted_reference"
                            )
                            components.append(_file_component(reference_kind, reference_path))
                        if reference_failed:
                            continue
                        layer3_failed = False
                        for name in layer3:
                            try:
                                layer3_path = _layer3_path(
                                    runtime_name, primary, str(name), manifest
                                )
                            except ValueError as exc:
                                errors.append(f"{case_id}: dispatch step {index}: {exc}")
                                layer3_failed = True
                                break
                            if not layer3_path.is_file():
                                errors.append(
                                    f"{case_id}: dispatch step {index} missing Layer 3 artifact "
                                    f"{_relative(layer3_path)}"
                                )
                                layer3_failed = True
                                break
                            components.append(_file_component("layer3", layer3_path))
                        if layer3_failed:
                            continue
                        layer3_reference_failed = False
                        for record_path in layer3_references:
                            try:
                                _record, nested_path = (
                                    _runtime_reference_record_and_target(
                                    DIST_SKILLS / runtime_name / primary,
                                    primary,
                                    str(record_path),
                                    )
                                )
                            except ValueError as exc:
                                errors.append(f"{case_id}: dispatch step {index}: {exc}")
                                layer3_reference_failed = True
                                break
                            if not nested_path.is_file() or _uses_symlink(
                                nested_path, DIST_SKILLS / runtime_name
                            ):
                                errors.append(
                                    f"{case_id}: dispatch step {index} missing or symlinked "
                                    f"Layer 3 Reference {_relative(nested_path)}"
                                )
                                layer3_reference_failed = True
                                break
                            components.append(
                                _file_component("layer3_reference", nested_path)
                            )
                        if layer3_reference_failed:
                            continue
                    components.append(
                        _component(
                            "dispatch_capsule",
                            f"fixture:{case_id}:step:{index}:canonical-capsule",
                            canonical_capsule,
                        )
                    )
                    measurement = _measure_context(
                        components,
                        budget_class=budget_class,
                    )
                    measurement.update(
                        {
                            "host": host,
                            "runtime": runtime_name,
                            "step": index,
                            "role": role,
                            "mode": raw_step.get("mode"),
                            "primary_skill": primary or None,
                            "layer3_skills": [str(item) for item in layer3],
                            "layer3_references": [
                                str(item) for item in layer3_references
                            ],
                            "loaded_layer3_reference_count": len(layer3_references),
                            "loaded_layer3_reference_logical_ids": [
                                str(item) for item in layer3_references
                            ],
                            "professional_references": list(references),
                            "canonical_capsule_tokens": count_o200k_base_tokens(
                                canonical_capsule
                            ),
                        }
                    )
                    if not measurement["within_duplicate_budget"]:
                        errors.append(
                            f"{case_id}:step:{index}:{host}:{runtime_name} duplicate ratio "
                            f"{measurement['duplicate_rule_token_ratio']:.3f} exceeds "
                            f"{DUPLICATE_TOKEN_RATIO_MAX:.2f}"
                        )
                    dispatch_results.append(measurement)
                    measurement_count += 1
        case_results.append(
            {
                "id": case_id,
                "fixture_group": fixture_group,
                "dispatch_count": sum(
                    isinstance(step, dict) and step.get("action") == "dispatch"
                    for step in steps
                ),
                "measurements": dispatch_results,
            }
        )

    discovery = _discovery_metadata(RUNTIME_NAME, errors)
    all_dispatch_measurements = [
        item
        for case in case_results
        for item in case["measurements"]
    ]
    fixture_layer3_reference_ids = [
        str(logical_id)
        for _fixture_group, case in cases
        for step in case.get("steps", [])
        if isinstance(step, dict) and step.get("action") == "dispatch"
        for logical_id in step.get("layer3_references", [])
    ]
    max_by_class: dict[str, dict[str, Any] | None] = {}
    for budget_class in ("analysis", "task", "analyzed_task", "review", "utility"):
        candidates = [
            item for item in all_dispatch_measurements if item["budget_class"] == budget_class
        ]
        maximum = max(candidates, key=lambda item: item["total_tokens"], default=None)
        max_by_class[budget_class] = _maximum_summary(
            maximum,
            include_dispatch=True,
        )
    max_main = max(main_contexts, key=lambda item: item["total_tokens"], default=None)
    duplicate_candidates = [*main_contexts, *all_dispatch_measurements]
    max_duplicate = max(
        duplicate_candidates,
        key=lambda item: item["duplicate_rule_token_ratio"],
        default=None,
    )
    duplicate_block_examples = (
        list(max_duplicate.get("duplicate_blocks", []))[:10]
        if max_duplicate
        else []
    )
    admissible_context_compositions = _evaluate_admissible_context_compositions(
        cases=cases,
        runtime_manifests={RUNTIME_NAME: runtime_manifest},
    )
    errors.extend(admissible_context_compositions["errors"])
    budget_governance = _budget_governance_report(
        mode=mode,
        main_contexts=main_contexts,
        dispatch_measurements=all_dispatch_measurements,
        admissible_context_compositions=admissible_context_compositions,
    )
    component_catalog = _compact_component_catalog(duplicate_candidates)
    errors.extend(
        f"{item['budget_class']} context maximum {item['tokens']} exceeds Core hard ceiling {item['hard_ceiling']}"
        for item in budget_governance["conformance_failures"]
    )
    return {
        "schema_version": 2,
        "status": "pass" if not errors else "fail",
        "evidence_scope": "deterministic-rendered-artifacts",
        "compiled_layer3_format": COMPILED_LAYER3_FORMAT,
        "tokenizer": "o200k_base",
        "limitations": list(LIMITATIONS),
        "runtime": RUNTIME_NAME,
        "hosts": list(HOST_PROFILE_ROOTS),
        "budget_governance": budget_governance,
        "fixture_count": len(case_results),
        "fixture_schema_version": document.get("schema_version"),
        "dispatch_count": dispatch_count,
        "measurement_count": measurement_count,
        "main_contexts": main_contexts,
        "discovery_metadata": discovery,
        "component_catalog": component_catalog,
        "cases": case_results,
        "admissible_context_compositions": admissible_context_compositions,
        "aggregate": {
            "max_main": (
                _maximum_summary(max_main, include_dispatch=False)
            ),
            "max_by_budget_class": max_by_class,
            "max_duplicate_rule_token_ratio": (
                max_duplicate["duplicate_rule_token_ratio"] if max_duplicate else None
            ),
            "duplicate_rule_token_ratio_margin": (
                round(
                    DUPLICATE_TOKEN_RATIO_MAX
                    - max_duplicate["duplicate_rule_token_ratio"],
                    6,
                )
                if max_duplicate
                else None
            ),
            "max_discovery_metadata_tokens": max(
                (discovery["tokens"],), default=None
            ),
            "loaded_layer3_reference_count": len(fixture_layer3_reference_ids),
            "measured_layer3_reference_component_count": sum(
                item.get("loaded_layer3_reference_count", 0)
                for item in all_dispatch_measurements
            ),
            "loaded_layer3_reference_logical_ids": sorted(
                set(fixture_layer3_reference_ids)
            ),
            "duplicate_block_examples_from_max_ratio_context": duplicate_block_examples,
        },
        "errors": errors,
    }


def _write_reports(report, *, release_projection=False, reports_dir=None):
    reports_dir = REPORT_JSON.parent if reports_dir is None else reports_dir
    out_json, out_md = report_output_paths(reports_dir, REPORT_JSON.name, REPORT_MD.name)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2) + "\n")
    if release_projection:
        out_md.write_text("# Rendered Instruction Context\n\nStatus: " + report["status"] + "\n\n" +
                          "\n".join("- " + item for item in report["limitations"]) + "\n")


def _args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("conformance", "calibration"), default="conformance")
    parser.add_argument("--release-projection", action="store_true")
    parser.add_argument("--reports-dir", type=Path, default=REPORT_JSON.parent)
    return parser.parse_args(argv)


def main(argv=None):
    args = _args(argv)
    with _subject_configuration(ROOT, FIXTURES, args.reports_dir / LIGHTWEIGHT_REPORT.name):
        try:
            report = evaluate(args.mode)
        except (ValueError, OSError) as exc:
            print(f"eval-rendered-context-budget: ERROR: {exc}", file=sys.stderr)
            return 1
    _write_reports(report, release_projection=args.release_projection, reports_dir=args.reports_dir)
    for error in report["errors"]:
        print(f"eval-rendered-context-budget: ERROR: {error}", file=sys.stderr)
    print(f"eval-rendered-context-budget: {report['dispatch_count']} dispatches, {len(report['hosts'])} hosts: {report['status']}")
    return int(bool(report["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
