#!/usr/bin/env python3
"""Measure deterministic rendered instruction context with exact token budgets."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

from validation_utils import (
    COMPILED_LAYER3_FORMAT,
    CONTEXT_BUDGET_MODEL,
    ValidationProblem,
    count_o200k_base_tokens,
    derived_context_budget_limits,
    load_yaml_file,
    parse_frontmatter,
    reference_paths,
)
from fixture_capsule_contract import (
    CONTRACT_VERSION as FIXTURE_CAPSULE_CONTRACT_VERSION,
    FixtureCapsuleError,
    parse_layer3_reference_id,
    trace_execution_level_migration_errors,
    validate_and_render_fixture_capsule,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "evals" / "agent-light-trajectories" / "cases.yaml"
DIST_SKILLS = ROOT / "dist" / "universal" / "skills"
CONTROL_PROMPT = ROOT / "src" / "control-prompts" / "main-control-agent.md"
REPORT_JSON = ROOT / "reports" / "rendered-context-budget.json"
REPORT_MD = ROOT / "reports" / "rendered-context-budget.md"

BUILD_PROFILES = ("recommended", "full", "dev")
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
CONTEXT_BUDGET_LIMITS = derived_context_budget_limits(CONTEXT_BUDGET_MODEL)
FROZEN_GATES = {
    budget_class: limit["evolution_target"]
    for budget_class, limit in CONTEXT_BUDGET_LIMITS.items()
}
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
    "Counts cover deterministic rendered ChangeForge instructions and canonical Capsules rendered from versioned checked-in fixture data, not a host-observed model request.",
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


def _measure_context(
    components: list[dict[str, Any]],
    *,
    budget_class: str,
    token_budget: int,
) -> dict[str, Any]:
    limit = CONTEXT_BUDGET_LIMITS[budget_class]
    if token_budget != limit["evolution_target"]:
        raise ValueError(
            f"{budget_class} token budget must equal its derived evolution target"
        )
    combined = "\n\n".join(component["_text"].rstrip() for component in components)
    total_tokens = count_o200k_base_tokens(combined)
    duplicates = _duplicate_block_metrics(components)
    duplicate_tokens = duplicates["duplicate_rule_tokens"]
    ratio = duplicate_tokens / total_tokens if total_tokens else 0.0
    public_components = [
        {key: value for key, value in component.items() if key != "_text"}
        for component in components
    ]
    return {
        "budget_class": budget_class,
        "capacity_ceiling": limit["capacity_ceiling"],
        "minimum_headroom_ratio": limit["minimum_headroom_ratio"],
        "required_reserve_tokens": limit["required_reserve_tokens"],
        "release_target": limit["release_target"],
        "minimum_release_margin_tokens": limit[
            "minimum_release_margin_tokens"
        ],
        "evolution_target": limit["evolution_target"],
        "token_budget": token_budget,
        "total_tokens": total_tokens,
        "sum_component_tokens": sum(item["tokens"] for item in public_components),
        "duplicate_rule_tokens": duplicate_tokens,
        "duplicate_rule_token_ratio": round(ratio, 6),
        "within_token_budget": total_tokens <= token_budget,
        "within_duplicate_budget": ratio <= DUPLICATE_TOKEN_RATIO_MAX,
        "components": public_components,
        "duplicate_blocks": duplicates["duplicate_blocks"],
    }


def _profile_path(host: str, role: str) -> Path:
    return HOST_PROFILE_ROOTS[host] / f"{role}{HOST_PROFILE_SUFFIXES[host]}"


def _load_manifests(errors: list[str]) -> dict[str, dict[str, Any]]:
    manifests: dict[str, dict[str, Any]] = {}
    for profile in BUILD_PROFILES:
        path = DIST_SKILLS / profile / ".changeforge-build-manifest.json"
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(
                f"{_relative(path)} is unavailable or malformed; run all three builds first: {exc}"
            )
            continue
        if not isinstance(value, dict) or value.get("profile") != profile:
            errors.append(f"{_relative(path)} does not describe profile {profile!r}")
            continue
        if value.get("compiled_layer3_format") != COMPILED_LAYER3_FORMAT:
            errors.append(
                f"{_relative(path)} compiled_layer3_format must equal "
                f"{COMPILED_LAYER3_FORMAT!r}"
            )
            continue
        manifests[profile] = value
    return manifests


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
    build_profile: str,
    primary: str,
    name: str,
    manifest: dict[str, Any],
) -> Path:
    compiled = manifest.get("compiled_layer3_references", {}).get(primary, [])
    is_compiled = name in compiled
    is_top_level = name in manifest.get("top_level_skills", [])
    if is_compiled == is_top_level:
        raise ValueError(
            f"{build_profile}:{primary} must resolve routed Layer 3 Skill {name!r} "
            "through exactly one compiled or top-level delivery path"
        )
    if is_compiled:
        return DIST_SKILLS / build_profile / primary / "references" / "layer3" / f"{name}.md"
    return DIST_SKILLS / build_profile / name / "SKILL.md"


def _layer3_reference_path(
    build_profile: str,
    primary: str,
    logical_id: str,
    manifest: dict[str, Any],
) -> Path:
    owner, relative = parse_layer3_reference_id(logical_id)
    compiled = manifest.get("compiled_layer3_references", {}).get(primary, [])
    is_compiled = owner in compiled
    is_top_level = owner in manifest.get("top_level_skills", [])
    if is_compiled == is_top_level:
        raise ValueError(
            f"{build_profile}:{primary} must resolve Layer 3 Reference owner {owner!r} "
            "through exactly one compiled or top-level delivery path"
        )
    if is_compiled:
        return (
            DIST_SKILLS
            / build_profile
            / primary
            / "references"
            / "layer3"
            / owner
            / relative
        )
    return DIST_SKILLS / build_profile / owner / relative


def _uses_symlink(path: Path, boundary: Path) -> bool:
    current = path
    while current != boundary and boundary in current.parents:
        if current.is_symlink():
            return True
        current = current.parent
    return current.is_symlink()


def _layer3_registry_entries() -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for registry_path, key in (
        (ROOT / "src/registry/foundation-skills.yaml", "foundation_skills"),
        (ROOT / "src/registry/domain-skills.yaml", "domain_skills"),
    ):
        document = load_yaml_file(registry_path)
        rows = document.get(key) if isinstance(document, dict) else None
        if not isinstance(rows, list):
            raise ValueError(f"{_relative(registry_path)} requires a {key} list")
        for row in rows:
            if isinstance(row, dict) and isinstance(row.get("name"), str):
                entries[row["name"]] = row
    return entries


def _layer3_reference_registry_errors(
    case_id: str,
    index: int,
    step: dict[str, Any],
    entries: dict[str, dict[str, Any]],
) -> list[str]:
    if "utility_capsule" in step:
        return []
    raw = step.get("layer3_references")
    if not isinstance(raw, list):
        return [f"{case_id}: dispatch step {index} layer3_references must be a list"]
    errors: list[str] = []
    for logical_id in raw:
        try:
            owner, relative = parse_layer3_reference_id(logical_id)
        except FixtureCapsuleError as exc:
            errors.append(f"{case_id}: dispatch step {index}: {exc}")
            continue
        entry = entries.get(owner)
        indexed = (
            reference_paths(
                entry.get("reference_index"),
                f"{owner}.reference_index",
                owner=owner,
            )
            if entry
            else []
        )
        if entry is None or relative not in indexed:
            errors.append(
                f"{case_id}: dispatch step {index} Layer 3 Reference "
                f"{logical_id!r} is not registry-indexed"
            )
            continue
        source = ROOT / str(entry.get("path", "")) / relative
        if not source.is_file() or _uses_symlink(source, ROOT):
            errors.append(
                f"{case_id}: dispatch step {index} Layer 3 Reference "
                f"{logical_id!r} is missing or symlinked in source"
            )
    return errors


def _professional_reference_path(
    build_profile: str,
    primary: str,
    relative: str,
) -> Path:
    if "\\" in relative:
        raise ValueError(f"professional reference must use POSIX syntax: {relative!r}")
    parsed = PurePosixPath(relative)
    if parsed.is_absolute() or any(part in {"", ".", ".."} for part in parsed.parts):
        raise ValueError(f"professional reference is not normalized: {relative!r}")
    if not parsed.parts or parsed.parts[0] != "references":
        raise ValueError(f"professional reference must remain under references/: {relative!r}")
    return DIST_SKILLS.joinpath(build_profile, primary, *parsed.parts)


def _has_authoritative_task_dag_provenance(
    step: dict[str, Any],
    case_kind: str,
    case_steps: list[Any],
) -> bool:
    if (
        case_kind != "direct"
        or step.get("profile") != "task-agent"
        or "utility_capsule" in step
    ):
        return False
    capsule = step.get("fixture_capsule")
    if not isinstance(capsule, dict) or capsule.get("contract_type") != "task":
        return False
    if capsule.get("inputs") != [
        "Accepted, artifact-reviewed authoritative Task DAG and downstream "
        "Task Capsule",
        "Current source, tests, routed Professional Skill, and named Layer 3 "
        "guidance",
    ]:
        return False
    dependencies = capsule.get("dependencies")
    if not isinstance(dependencies, list) or len(dependencies) != 1:
        return False
    dependency = dependencies[0]
    template = capsule.get("template")
    if template == "implementation-task":
        if dependency not in (
            "Accepted authoritative Task DAG node and engineering-artifact-review "
            "pass.",
            "Accepted authoritative Task DAG dependency plus completed predecessor "
            "output and current evidence.",
        ):
            return False
    elif template == "integration-task":
        if dependency != (
            "Completed authoritative Task DAG predecessor outputs and their "
            "current evidence."
        ):
            return False
    else:
        return False
    if any(
        isinstance(candidate, dict)
        and candidate.get("action") == "dispatch"
        and candidate.get("profile") == "analysis-agent"
        for candidate in case_steps
    ):
        return False
    authoritative_evidence = (
        "Accepted, artifact-reviewed authoritative Task DAG selects three "
        "downstream integration tasks and final review.",
        "Accepted, artifact-reviewed authoritative Task DAG selects two "
        "serialized downstream tasks and final review.",
    )
    return any(
        isinstance(candidate, dict)
        and candidate.get("action") == "progress"
        and candidate.get("evidence") in authoritative_evidence
        for candidate in case_steps
    )


def _budget_class(
    step: dict[str, Any],
    case_kind: str,
    case_steps: list[Any],
) -> str:
    profile = step.get("profile")
    if profile == "analysis-agent":
        return "analysis"
    if profile == "review-agent":
        return "review"
    if profile == "task-agent" and "utility_capsule" in step:
        return "utility"
    if profile == "task-agent":
        if case_kind == "analyzed" or _has_authoritative_task_dag_provenance(
            step,
            case_kind,
            case_steps,
        ):
            return "analyzed_task"
        return "task"
    raise ValueError(f"unsupported dispatch profile {profile!r}")


def _fixture_cases(document: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    result: list[tuple[str, dict[str, Any]]] = []
    for group, key in (
        ("release", "cases"),
        ("scheduling", "scheduling_cases"),
        ("utility", "utility_cases"),
    ):
        raw_cases = document.get(key)
        if not isinstance(raw_cases, list):
            raise ValueError(f"fixture document requires a {key} list")
        for case in raw_cases:
            if not isinstance(case, dict):
                raise ValueError(f"{key} entries must be mappings")
            result.append((group, case))
    if not result:
        raise ValueError("fixture document must contain at least one case")
    return result


def _dispatch_metadata_errors(case_id: str, index: int, step: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        validate_and_render_fixture_capsule(step)
    except FixtureCapsuleError as exc:
        errors.append(f"{case_id}: dispatch step {index} has invalid fixture Capsule: {exc}")
    mode = step.get("mode")
    if not isinstance(mode, str) or not mode.strip():
        errors.append(f"{case_id}: dispatch step {index} needs a non-empty mode")
    references = step.get("professional_references")
    if not isinstance(references, list) or any(
        not isinstance(item, str) or not item.strip() for item in references
    ):
        errors.append(
            f"{case_id}: dispatch step {index} needs a professional_references string list"
        )
        references = []
    if len(references) != len(set(references)):
        errors.append(f"{case_id}: dispatch step {index} repeats a professional reference")
    primary = step.get("primary_skill")
    if primary == "engineering-change-analysis":
        expected_reference = MODE_REFERENCES.get(str(mode))
        if expected_reference is None:
            errors.append(f"{case_id}: dispatch step {index} has unsupported analysis mode {mode!r}")
        elif expected_reference not in references:
            errors.append(
                f"{case_id}: dispatch step {index} must load mode reference {expected_reference!r}"
            )
    if "utility_capsule" in step:
        utility_mode = step.get("utility_capsule", {}).get("mode")
        if mode != utility_mode:
            errors.append(f"{case_id}: dispatch step {index} utility mode does not match capsule")
        if references:
            errors.append(f"{case_id}: dispatch step {index} utility must not load references")
        if "layer3_references" in step:
            errors.append(
                f"{case_id}: dispatch step {index} utility must not declare layer3_references"
            )
    return errors


def _discovery_metadata(
    build_profile: str,
    errors: list[str],
) -> dict[str, Any]:
    root = DIST_SKILLS / build_profile
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
        "build_profile": build_profile,
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
    """Expose both release margin and capacity headroom for one maximum."""

    if maximum is None:
        return None
    ceiling = maximum["capacity_ceiling"]
    observed = maximum["total_tokens"]
    result = {
        "tokens": observed,
        "capacity_ceiling": ceiling,
        "minimum_headroom_ratio": maximum["minimum_headroom_ratio"],
        "required_reserve_tokens": maximum["required_reserve_tokens"],
        "release_target": maximum["release_target"],
        "minimum_release_margin_tokens": maximum[
            "minimum_release_margin_tokens"
        ],
        "evolution_target": maximum["evolution_target"],
        "release_margin_tokens": maximum["release_target"] - observed,
        "evolution_margin_tokens": maximum["evolution_target"] - observed,
        "capacity_headroom_tokens": ceiling - observed,
        "capacity_headroom_ratio": round((ceiling - observed) / ceiling, 6),
        "host": maximum["host"],
        "build_profile": maximum["build_profile"],
    }
    if include_dispatch:
        result.update(
            {
                "step": maximum["step"],
                "primary_skill": maximum["primary_skill"],
            }
        )
    return result


def evaluate() -> dict[str, Any]:
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
    layer3_entries = _layer3_registry_entries()
    manifests = _load_manifests(errors)
    if set(manifests) != set(BUILD_PROFILES):
        raise ValueError("all recommended/full/dev build manifests are required")

    prompt_tokens = count_o200k_base_tokens(CONTROL_PROMPT.read_text(encoding="utf-8"))
    main_contexts: list[dict[str, Any]] = []
    for host in HOST_PROFILE_ROOTS:
        profile_path = _profile_path(host, "main-control-agent")
        if not profile_path.is_file():
            errors.append(f"missing rendered Profile {_relative(profile_path)}")
            continue
        for build_profile in BUILD_PROFILES:
            _validate_profile_digest(
                host,
                "main-control-agent",
                profile_path,
                manifests[build_profile],
                errors,
            )
            control_skill = DIST_SKILLS / build_profile / "engineering-control-plane" / "SKILL.md"
            if not control_skill.is_file():
                errors.append(f"missing built Control Skill {_relative(control_skill)}")
                continue
            measurement = _measure_context(
                [
                    _file_component("rendered_main_profile", profile_path),
                    _file_component("control_skill", control_skill),
                ],
                budget_class="main",
                token_budget=FROZEN_GATES["main"],
            )
            measurement.update(
                {
                    "host": host,
                    "build_profile": build_profile,
                    "embedded_control_prompt_tokens": prompt_tokens,
                    "control_prompt_accounting": (
                        "included in rendered_main_profile and not added as a separate component"
                    ),
                }
            )
            if not measurement["within_token_budget"]:
                errors.append(
                    f"main:{host}:{build_profile} uses {measurement['total_tokens']} tokens; "
                    f"budget is {measurement['token_budget']}"
                )
            if not measurement["within_duplicate_budget"]:
                errors.append(
                    f"main:{host}:{build_profile} duplicate ratio "
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
            step_errors = _dispatch_metadata_errors(case_id, index, raw_step)
            step_errors.extend(
                f"{case_id}: dispatch step {index} {error}"
                for error in trace_execution_level_migration_errors(steps, index)
            )
            step_errors.extend(
                _layer3_reference_registry_errors(
                    case_id, index, raw_step, layer3_entries
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
                for build_profile in BUILD_PROFILES:
                    _validate_profile_digest(
                        host,
                        role,
                        profile_path,
                        manifests[build_profile],
                        errors,
                    )
                    components = [_file_component("worker_profile", profile_path)]
                    manifest = manifests[build_profile]
                    if primary:
                        primary_path = DIST_SKILLS / build_profile / primary / "SKILL.md"
                        if not primary_path.is_file():
                            errors.append(f"missing primary Skill {_relative(primary_path)}")
                            continue
                        components.append(_file_component("primary_skill", primary_path))
                        reference_failed = False
                        for reference in references:
                            try:
                                reference_path = _professional_reference_path(
                                    build_profile, primary, reference
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
                                    build_profile, primary, str(name), manifest
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
                        for logical_id in layer3_references:
                            try:
                                nested_path = _layer3_reference_path(
                                    build_profile,
                                    primary,
                                    str(logical_id),
                                    manifest,
                                )
                            except (FixtureCapsuleError, ValueError) as exc:
                                errors.append(f"{case_id}: dispatch step {index}: {exc}")
                                layer3_reference_failed = True
                                break
                            if not nested_path.is_file() or _uses_symlink(
                                nested_path, DIST_SKILLS / build_profile
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
                        token_budget=FROZEN_GATES[budget_class],
                    )
                    measurement.update(
                        {
                            "host": host,
                            "build_profile": build_profile,
                            "step": index,
                            "role": role,
                            "mode": raw_step["mode"],
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
                            "capsule_contract_version": FIXTURE_CAPSULE_CONTRACT_VERSION,
                            "canonical_capsule_sha256": raw_step["fixture_capsule"][
                                "canonical_sha256"
                            ],
                            "canonical_capsule_tokens": count_o200k_base_tokens(
                                canonical_capsule
                            ),
                        }
                    )
                    if not measurement["within_token_budget"]:
                        errors.append(
                            f"{case_id}:step:{index}:{host}:{build_profile} uses "
                            f"{measurement['total_tokens']} {budget_class} tokens; "
                            f"budget is {measurement['token_budget']}"
                        )
                    if not measurement["within_duplicate_budget"]:
                        errors.append(
                            f"{case_id}:step:{index}:{host}:{build_profile} duplicate ratio "
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

    discovery = [
        _discovery_metadata(build_profile, errors)
        for build_profile in BUILD_PROFILES
    ]
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
    component_catalog = _compact_component_catalog(duplicate_candidates)
    return {
        "schema_version": 2,
        "status": "pass" if not errors else "fail",
        "evidence_scope": "deterministic-rendered-artifacts",
        "compiled_layer3_format": COMPILED_LAYER3_FORMAT,
        "tokenizer": "o200k_base",
        "fixture_capsule_contract": {
            "version": FIXTURE_CAPSULE_CONTRACT_VERSION,
            "source": "scripts/fixture_capsule_contract.py",
            "placement": "evaluator-only; excluded from build and installation artifacts",
            "hash_role": "detects unsynchronized canonical rendered text",
            "semantic_gate": (
                "field-specific prose, repository path/glob, command, input, "
                "explicit Layer 3 Reference logical ID, and Utility-schema minimums"
            ),
        },
        "limitations": list(LIMITATIONS),
        "build_profiles": list(BUILD_PROFILES),
        "hosts": list(HOST_PROFILE_ROOTS),
        "budget_calibration": {
            "method": (
                "Capacity ceilings and minimum headroom ratios come from the Core Model; "
                "release and evolution targets are derived without calibration relaxation."
            ),
            "source": "src/control-model/core-contracts.json#/context_budget_contract",
            "capacity_ceilings": {
                key: value["capacity_ceiling"]
                for key, value in CONTEXT_BUDGET_LIMITS.items()
            },
            "minimum_headroom_ratios": {
                key: value["minimum_headroom_ratio"]
                for key, value in CONTEXT_BUDGET_LIMITS.items()
            },
            "required_reserve_tokens": {
                key: value["required_reserve_tokens"]
                for key, value in CONTEXT_BUDGET_LIMITS.items()
            },
            "release_targets": {
                key: value["release_target"]
                for key, value in CONTEXT_BUDGET_LIMITS.items()
            },
            "minimum_release_margin_tokens": {
                key: value["minimum_release_margin_tokens"]
                for key, value in CONTEXT_BUDGET_LIMITS.items()
            },
            "evolution_targets": dict(FROZEN_GATES),
            "frozen_gates": dict(FROZEN_GATES),
            "relaxations": [],
            "duplicate_rule_token_ratio_max": DUPLICATE_TOKEN_RATIO_MAX,
        },
        "fixture_count": len(case_results),
        "fixture_schema_version": document.get("schema_version"),
        "dispatch_count": dispatch_count,
        "measurement_count": measurement_count,
        "main_contexts": main_contexts,
        "discovery_metadata": discovery,
        "component_catalog": component_catalog,
        "cases": case_results,
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
                (item["tokens"] for item in discovery), default=None
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


def _write_reports(report: dict[str, Any]) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    aggregate = report["aggregate"]
    lines = [
        "# Rendered Context Budget Evaluation",
        "",
        f"Status: **{report['status']}**",
        "",
        f"Evidence scope: **{report['evidence_scope']}**",
        "",
        f"Compiled Layer 3 format: **{report['compiled_layer3_format']}**",
        "",
        f"Tokenizer: **{report['tokenizer']}**",
        "",
        f"Fixtures: **{report['fixture_count']}**; dispatches: **{report['dispatch_count']}**; "
        f"host/profile measurements: **{report['measurement_count']}**.",
        f"Explicit nested Layer 3 Reference loads: "
        f"**{aggregate['loaded_layer3_reference_count']}**; logical IDs: "
        f"**{', '.join(aggregate['loaded_layer3_reference_logical_ids']) or 'none'}**.",
        f"Measured nested Reference components across host/profile combinations: "
        f"**{aggregate['measured_layer3_reference_component_count']}**.",
        "",
        f"Fixture Capsule contract: **{report['fixture_capsule_contract']['version']}**. "
        "Its hash detects drift, its typed semantic gate rejects synchronized "
        "placeholder/low-diversity forgeries, and its deterministic renderer is "
        "evaluator-only and excluded from build/install artifacts.",
        "",
        "The Control Prompt is embedded in each rendered Main Profile and is not added a second time.",
        "",
        "## Authoritative Limits and Observed Maxima",
        "",
        "Capacity ceilings, minimum headroom ratios, and minimum release margins "
        "come from the Core Model. Release and evolution targets are derived; "
        "calibration relaxations: **none**.",
        "",
        "| Context | Capacity ceiling | Required reserve | Release target | Minimum release margin | Evolution target | Observed maximum | Release margin | Evolution margin | Capacity headroom ratio |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    main = aggregate["max_main"]
    lines.append(
        f"| Main always-loaded | {main['capacity_ceiling'] if main else 'n/a'} | "
        f"{main['required_reserve_tokens'] if main else 'n/a'} | "
        f"{main['release_target'] if main else 'n/a'} | "
        f"{main['minimum_release_margin_tokens'] if main else 'n/a'} | "
        f"{main['evolution_target'] if main else 'n/a'} | "
        f"{main['tokens'] if main else 'n/a'} | "
        f"{main['release_margin_tokens'] if main else 'n/a'} | "
        f"{main['evolution_margin_tokens'] if main else 'n/a'} | "
        f"{main['capacity_headroom_ratio'] if main else 'n/a'} |"
    )
    for budget_class in ("task", "analyzed_task", "analysis", "review", "utility"):
        maximum = aggregate["max_by_budget_class"].get(budget_class)
        lines.append(
            f"| {CONTEXT_BUDGET_LIMITS[budget_class]['label']} | "
            f"{maximum['capacity_ceiling'] if maximum else 'n/a'} | "
            f"{maximum['required_reserve_tokens'] if maximum else 'n/a'} | "
            f"{maximum['release_target'] if maximum else 'n/a'} | "
            f"{maximum['minimum_release_margin_tokens'] if maximum else 'n/a'} | "
            f"{maximum['evolution_target'] if maximum else 'n/a'} | "
            f"{maximum['tokens'] if maximum else 'n/a'} | "
            f"{maximum['release_margin_tokens'] if maximum else 'n/a'} | "
            f"{maximum['evolution_margin_tokens'] if maximum else 'n/a'} | "
            f"{maximum['capacity_headroom_ratio'] if maximum else 'n/a'} |"
        )
    lines.extend(
        [
            "",
            f"Maximum exact normalized duplicate-rule ratio: "
            f"**{aggregate['max_duplicate_rule_token_ratio']}** "
            f"(gate: **{DUPLICATE_TOKEN_RATIO_MAX}**; margin: "
            f"**{aggregate['duplicate_rule_token_ratio_margin']}**).",
            "",
            "Discovery metadata is reported separately because actual host discovery injection is not observed.",
            "",
            "## Limitations",
            "",
            *[f"- {item}" for item in report["limitations"]],
            "",
        ]
    )
    if report["errors"]:
        lines.extend(["## Errors", "", *[f"- {item}" for item in report["errors"]], ""])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    try:
        report = evaluate()
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"eval-rendered-context-budget: ERROR: {exc}", file=sys.stderr)
        return 1
    _write_reports(report)
    if report["errors"]:
        for error in report["errors"]:
            print(f"eval-rendered-context-budget: ERROR: {error}", file=sys.stderr)
        return 1
    print(
        "eval-rendered-context-budget: validated "
        f"{report['dispatch_count']} dispatches across "
        f"{len(report['hosts'])} hosts and {len(report['build_profiles'])} build profiles."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
