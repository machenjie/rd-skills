#!/usr/bin/env python3
"""Validate current rd-skills human documentation and source-owned facts."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
INSTALLER_DIR = ROOT / "installers"
for import_dir in (SCRIPT_DIR, INSTALLER_DIR):
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

from changeforge_install import (  # noqa: E402
    AGENTS as INSTALLER_AGENTS,
    DEFAULT_PROFILE_TARGETS,
    DEFAULT_SKILL_TARGETS,
    PROJECT_PROFILE_SUBPATHS,
    PROJECT_SKILL_SUBPATHS,
    RUNTIME_PROFILE,
    RUNTIME_SKILL_COUNT,
    SOURCE_PROFILE_ROOTS,
    SOURCE_SKILL_ROOTS,
    InstallError,
    read_host_product_surfaces,
)

from validation_utils import (  # noqa: E402
    AUTHORITATIVE_BUILD_INPUT_EXCLUDED_PATHS,
    ValidationProblem,
    context_budget_docs_projection_block,
    derived_context_budget_limits,
    docs_projection_block,
    load_core_contracts,
    load_yaml_file,
)


REGISTRY_SPECS = {
    "control": ("src/registry/control-skills.yaml", "control_skills"),
    "professional": (
        "src/registry/professional-skills.yaml",
        "professional_skills",
    ),
    "foundation": ("src/registry/foundation-skills.yaml", "foundation_skills"),
    "domain": ("src/registry/domain-skills.yaml", "domain_skills"),
}
VOLATILE_FACT_DOCS = (
    "AGENTS.md",
    ".github/pull_request_template.md",
    "docs/BUILD_PROFILES.md",
    "docs/VALIDATION.md",
    "docs/SCORECARD.md",
    "docs/BENCHMARKS.md",
)
CURRENT_EVIDENCE_DOCS = (
    "GOVERNANCE.md",
    ".github/pull_request_template.md",
    "docs/RELEASE.md",
    "docs/VALIDATION.md",
    "docs/SKILL_CONTENT_GOVERNANCE.md",
    "docs/skill_professionalism_standard/SKILL_PROFESSIONALISM_EVALUATION_AND_GOVERNANCE.md",
)
STATIC_EVIDENCE_PROOF_LIMIT_DOCS = (
    "README.md",
    "docs/QUALITY_MODEL.md",
    "docs/BENCHMARKS.md",
    "docs/README.md",
    "docs/RELEASE.md",
    "docs/VALIDATION.md",
    "docs/SCORECARD.md",
    "docs/skill_professionalism_standard/SKILL_PROFESSIONALISM_EVALUATION_AND_GOVERNANCE.md",
)
HOST_INVOCATION_ONBOARDING_DOCS = (
    "README.md",
    "docs/QUICKSTART.md",
    "docs/USAGE.md",
)
SHELL_FENCE_LANGUAGES = frozenset({"bash", "sh", "shell", "zsh"})
SHELL_PLACEHOLDER_RE = re.compile(
    r"<[A-Za-z][^>\n]*>|^\s*\[--|\b(?:YYYY-MM-DD|READABILITY_ID|"
    r"COMPLETENESS_ID|PRIOR_COMPLETENESS_ID|FRESH_AUDIT|REVIEW_ID|"
    r"REVIEWER_ID|AGENT_ID|SENIOR_ROLE|EXPERTISE|PACKET|BALLOT_TEMPLATE|"
    r"TEMPLATE_SHA256|MANIFEST_BYTES|MANIFEST_SHA256|BALLOT|"
    r"COMPLETED_BALLOT|REVIEWER_[ABC])(?:\.json)?\b",
    re.MULTILINE,
)
INSTALL_CONTRACT_SOURCE = "installers/changeforge_install.py"
HOST_PRODUCT_SURFACES_SOURCE = "src/agent-profiles/host-product-surfaces.json"
SCOPE_ORDER = ("project", "user", "admin")
COMMAND_VALIDATION_SCOPE = (
    "documented Python script/installer targets exist; retired Runtime flags are "
    "rejected on public and authoring surfaces"
)
GOVERNANCE_BUDGET_REPORT = "reports/rendered-context-budget.json"
GOVERNANCE_BUDGET_BEGIN = (
    "<!-- BEGIN CHANGEFORGE GOVERNANCE CONTEXT BUDGET AUTHORITY -->"
)
GOVERNANCE_BUDGET_END = (
    "<!-- END CHANGEFORGE GOVERNANCE CONTEXT BUDGET AUTHORITY -->"
)
GOVERNANCE_EVIDENCE_AUTHORITIES = {
    "RDS-002": (
        "src/control-model/core-contracts.json",
        "tests/scripts/test_validate_agent_profiles.py",
        "tests/scripts/test_eval_agent_lightweight_utility.py",
    ),
    "RDS-003": (
        "src/control-model/core-contracts.json",
        "src/agent-profiles/role-agents.json",
        "tests/scripts/test_validate_agent_profiles.py",
    ),
    "RDS-009": ("tests/scripts/test_eval_agent_lightweight_utility.py",),
    "RDS-010": ("reports/installation-validation.json",),
}
GOVERNANCE_HISTORICAL_EVIDENCE_LABEL = (
    "- **Historical, non-current resolution evidence:**"
)
GOVERNANCE_VOLATILE_EVIDENCE_PATTERNS = (
    re.compile(
        r"\bprojects?\b[^\n]{0,120}\bthrough\s+\d+\s+(?:exact\s+)?rules?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bTask\s+Profile\s+(?:has|remains\s+at|contains|uses)\s+"
        r"\d+[^\n]{0,100}\brules?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:test|utility)\s+module\b[^\n]{0,80}\bpassed\s+"
        r"(?:all\s+)?\d+\s+tests?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b\d+\s*-\s*path\s*[×x]\s*\d+\s*-\s*guard\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+"
        r"focused[^\n]{0,80}\btests?\s+passed\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bpassed\s+with\s+\d+\s+required-behavior\s+entries\b",
        re.IGNORECASE,
    ),
)
ROOT_HUMAN_DOCS = (
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "SECURITY.md",
    "SUPPORT.md",
    ".github/pull_request_template.md",
    "reports/README.md",
    "evals/agent-behavior/README.md",
    "evals/codegen/README.md",
    "evals/pressure/README.md",
)
REQUIRED_DOCS = (
    "README.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "SECURITY.md",
    "SUPPORT.md",
    ".github/pull_request_template.md",
    "docs/README.md",
    "docs/AGENT_LIGHT_ARCHITECTURE.md",
    "docs/HOOKLESS_ARCHITECTURE.md",
    "docs/AI_CONTROL_BOUNDARIES.md",
    "docs/MIGRATING_TO_HOOKLESS.md",
    "docs/QUICKSTART.md",
    "docs/INSTALLATION.md",
    "docs/BUILD_PROFILES.md",
    "docs/OPERATING_MODEL.md",
    "docs/SUBAGENT_MODEL.md",
    "docs/USAGE.md",
    "docs/VALIDATION.md",
    "docs/BENCHMARKS.md",
    "docs/MARKETPLACE.md",
    "docs/MARKETPLACE_CATALOG.md",
    "docs/RELEASE.md",
    "docs/SKILL_CONTENT_GOVERNANCE.md",
    "reports/README.md",
    "evals/agent-behavior/README.md",
    "evals/codegen/README.md",
    "evals/pressure/README.md",
)
FORBIDDEN_USER_TOKENS = (
    "--with-hooks",
    "--without-hooks",
    "--hook-profile",
    "PreToolUse",
    "PostToolUse",
    ".changeforge-packs",
)
RETIRED_RUNTIME_FLAGS = (
    "--profile",
    "--with-hooks",
    "--without-hooks",
    "--hook-profile",
    "--professional-injection",
    "--activation-level",
)
RUNTIME_SURFACE_FILES = (
    "pyproject.toml",
    "Makefile",
    "SUPPORT.md",
    ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/ISSUE_TEMPLATE/feature_request.md",
    ".github/ISSUE_TEMPLATE/skill_change.md",
    "src/foundation/capabilities/README.md",
    (
        "src/foundation/capabilities/repository-context-map/references/"
        "source-generated-boundary-map.md"
    ),
    (
        "src/foundation/capabilities/skill-authoring-expert/references/"
        "evidence-patterns.md"
    ),
    "src/foundation/capabilities/skill-authoring-expert/SKILL.md",
    (
        "src/foundation/capabilities/skill-efficacy-benchmark/references/"
        "benchmarks-and-patterns.md"
    ),
    (
        "src/foundation/capabilities/skill-efficacy-benchmark/references/"
        "evidence-patterns.md"
    ),
)
RUNTIME_PROFILE_CHOICE_HISTORY_DOCS = frozenset(
    {"CHANGELOG.md", "GOVERNANCE.md", "docs/MIGRATING_TO_HOOKLESS.md"}
)
RUNTIME_PROFILE_CHOICE_PATTERNS = (
    re.compile(
        r"\bchoose\s+(?:a\s+)?(?:build\s+|install\s+|runtime\s+)?profile\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bbuild\s+profiles?\s+affected\b", re.IGNORECASE),
    re.compile(r"^\|\s*`(?:full|dev)`\s*\|", re.IGNORECASE | re.MULTILINE),
    re.compile(
        r"\b(?:select|specify)\s+`?(?:recommended|full|dev)`?\s+"
        r"(?:profile|runtime)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bbuild\s+profiles?\b", re.IGNORECASE),
    re.compile(
        r"\b(?:profile\s+delivery|generated\s+profiles|public\s+profile|"
        r"build-profile(?:\s+(?:output|map))?)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bselected\s+profile\b", re.IGNORECASE),
    re.compile(
        r"\bprofile(?:\s+impact)?\s*:[^\n]*\b(?:full|dev)\b",
        re.IGNORECASE,
    ),
)
LAYER3_CARDINALITY_GUIDANCE_FILES = (
    "docs/SKILL_CONTENT_GOVERNANCE.md",
    "docs/skill_authoring_standard/PROFESSIONAL_SKILL_AUTHORING_STANDARD.md",
)
LAYER3_CARDINALITY_GUIDANCE_FACTS = (
    "Layer 3 selection is an ordered unique list of zero to three items.",
    "More than three items or any duplicate fails closed; never truncate the selection.",
    "Higher risk changes which Layer 3 items are selected, not the maximum count.",
)
SOFTENED_LAYER3_CARDINALITY_PATTERNS = (
    re.compile(
        r"\bnormally\b[^\n]{0,100}\b(?:zero\s+to\s+three|0\s*(?:\.\.|to)\s*3)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:may|can)\s+(?:use|select|load)\s+more\b",
        re.IGNORECASE,
    ),
    re.compile(r"\brisk[- ]rationale\b", re.IGNORECASE),
)
DELETED_PATH_MARKERS = (
    "src/hook-runtime",
    "src/runtime_governance",
    "src/project_memory",
    "src/repository_intelligence",
    "src/validation_broker",
)
FORBIDDEN_CURRENT_TERMS = (
    "changeforge skill mesh",
    "hook behavior",
    "stage routing",
)
HISTORICAL_TERM_DOCS = {
    "CHANGELOG.md",
    "docs/MIGRATING_TO_HOOKLESS.md",
}
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
COMMAND_TARGET_RE = re.compile(
    r"\bpython3\s+((?:scripts|installers)/[A-Za-z0-9_.-]+\.py)"
)
FENCE_RE = re.compile(r"^\s{0,3}(?P<marker>`{3,}|~{3,})")
REQUIRED_NAVIGATION = {
    "docs/AGENT_LIGHT_ARCHITECTURE.md": (
        "docs/HOOKLESS_ARCHITECTURE.md",
        "docs/AI_CONTROL_BOUNDARIES.md",
        "docs/OPERATING_MODEL.md",
        "docs/SUBAGENT_MODEL.md",
    ),
    "README.md": (
        "docs/README.md",
        "docs/QUICKSTART.md",
        "docs/INSTALLATION.md",
        "docs/USAGE.md",
    ),
    "docs/QUICKSTART.md": (
        "docs/INSTALLATION.md",
        "docs/USAGE.md",
    ),
    "docs/INSTALLATION.md": (
        "docs/QUICKSTART.md",
        "docs/USAGE.md",
    ),
    "docs/USAGE.md": (
        "SUPPORT.md",
        "docs/AI_CONTROL_BOUNDARIES.md",
        "docs/HOOKLESS_ARCHITECTURE.md",
        "docs/INSTALLATION.md",
        "docs/MIGRATING_TO_HOOKLESS.md",
    ),
    "docs/README.md": (
        "docs/AI_CONTROL_BOUNDARIES.md",
        "docs/BENCHMARKS.md",
        "docs/BUILD_PROFILES.md",
        "docs/HOOKLESS_ARCHITECTURE.md",
        "docs/INSTALLATION.md",
        "docs/MARKETPLACE.md",
        "docs/MARKETPLACE_CATALOG.md",
        "docs/MIGRATING_TO_HOOKLESS.md",
        "docs/OPEN_SOURCE_READINESS.md",
        "docs/OPERATING_MODEL.md",
        "docs/QUALITY_MODEL.md",
        "docs/QUICKSTART.md",
        "docs/RELEASE.md",
        "docs/SCORECARD.md",
        "docs/SHOWCASE.md",
        "docs/SKILL_CONTENT_GOVERNANCE.md",
        "docs/SUBAGENT_MODEL.md",
        "docs/USAGE.md",
        "docs/VALIDATION.md",
        "docs/skill_authoring_standard/SKILL_AUTHORING_BASE_STANDARD.md",
        "docs/skill_authoring_standard/PROFESSIONAL_SKILL_AUTHORING_STANDARD.md",
        "docs/skill_authoring_standard/FOUNDATION_CAPABILITY_AUTHORING_STANDARD.md",
        "docs/skill_authoring_standard/DOMAIN_EXTENSION_AUTHORING_STANDARD.md",
        "docs/skill_professionalism_standard/SKILL_PROFESSIONALISM_BASE_STANDARD.md",
        "docs/skill_professionalism_standard/SKILL_PROFESSIONALISM_DIMENSION_RUBRIC.md",
        "docs/skill_professionalism_standard/SKILL_PROFESSIONALISM_EVALUATION_AND_GOVERNANCE.md",
        "examples/README.md",
        "reports/README.md",
        "evals/agent-behavior/README.md",
        "evals/codegen/README.md",
        "evals/pressure/README.md",
    ),
}
README_FIRST_SURFACE_FORBIDDEN = (
    "runtime",
    "layer 3",
    "foundation",
    "domain",
    "engineering brief",
    "execution level",
    "evidence ledger",
    "review boundary",
    "manifest",
    "digest",
    "fingerprint",
    "validator",
    "benchmark",
)
BEGINNER_PROTOCOL_TUTORIAL_TERMS = (
    "direct task",
    "analyzed work",
    "primary professional",
    "layer 3",
    "review input ready",
    "repair round",
    "evidence ledger",
    "effective level",
    "engineering brief",
    "execution level",
)
DEVELOPMENT_AFFECTED_COMMANDS = (
    "python3 scripts/eval-core-principles.py --gate affected --base <base> --head <head>",
    "python3 scripts/run-ci-tests.py run --base <base> --head <head>",
)
FULL_REGRESSION_COMMANDS = (
    "python3 scripts/eval-core-principles.py --gate authoring",
    "python3 scripts/validate-examples.py",
    "python3 scripts/generate-examples-showcase.py --out docs/SHOWCASE.md --check",
    "python3 scripts/generate-marketplace-catalog.py --out docs/MARKETPLACE_CATALOG.md --check",
    "python3 scripts/validate-marketplace-index.py",
    "python3 scripts/validate-productization-assets.py",
    "python3 scripts/validate-open-source-readiness.py --require-pass",
    "python3 scripts/run-ci-tests.py full --jobs 4 --timeout 900",
    "python3 scripts/validate-codegen-benchmarks.py",
    "python3 scripts/run-codegen-benchmarks.py --limit 3",
    "python3 scripts/quickstart.py --agent codex --scope user --dry-run",
    "python3 scripts/quickstart.py --agent claude --scope project --target /tmp/changeforge-quickstart-claude --dry-run",
    "python3 scripts/quickstart.py --agent copilot --scope project --target /tmp/changeforge-quickstart-copilot --dry-run",
    "python3 scripts/quickstart.py --agent openai-api --dry-run",
)
TEST_TIMEOUT_GUIDANCE_FACTS = (
    (
        "`--timeout` is the base duration in seconds for every test module "
        "executed by `_execute_modules`, including affected `run` and both Full "
        "execution lanes."
    ),
    (
        "An absent `TEST_TIMEOUT_CLASS` declaration or `standard` applies `1x` "
        "the base timeout; `source-validation` applies `2x`."
    ),
    (
        "`TEST_TIMEOUT_CLASS` must be declared at most once as a top-level static "
        "string literal from the closed set `standard` and `source-validation`."
    ),
    "Duplicate, nested, dynamic, or unknown declarations fail selection.",
)
RETIRED_WORKFLOW_PATHS = (
    ".github/workflows/ci.yml",
    ".github/workflows/formal-release.yml",
)
RETIRED_WORKFLOW_CLAIM_DOCS = (
    "AGENTS.md",
    "CONTRIBUTING.md",
    ".github/pull_request_template.md",
    "GOVERNANCE.md",
    "docs/RELEASE.md",
    "docs/VALIDATION.md",
    "docs/SKILL_CONTENT_GOVERNANCE.md",
    "docs/skill_professionalism_standard/SKILL_PROFESSIONALISM_EVALUATION_AND_GOVERNANCE.md",
)
RETIRED_REMOTE_REQUIRED_CLAIMS = (
    re.compile(r"\bPull-request CI\b", re.IGNORECASE),
    re.compile(r"\bCI / pr-ci\b", re.IGNORECASE),
    re.compile(r"unsharded `pr-ci` job", re.IGNORECASE),
    re.compile(r"remote `Formal Release` workflow", re.IGNORECASE),
    re.compile(r"same-commit remote workflow", re.IGNORECASE),
    re.compile(r"remote formal evidence", re.IGNORECASE),
    re.compile(r"\.github/workflows/formal-release\.yml", re.IGNORECASE),
    re.compile(r"workflow verifies the manifest commit", re.IGNORECASE),
    re.compile(r"uploaded by CI", re.IGNORECASE),
)


def _markdown_files(root: Path) -> list[Path]:
    files = [root / relative for relative in ROOT_HUMAN_DOCS]
    for directory in (root / "docs", root / "examples"):
        if directory.is_dir():
            files.extend(sorted(directory.rglob("*.md")))
    return sorted({path for path in files if path.is_file()})


def _without_fenced_examples(text: str) -> str:
    """Blank fenced examples so sample links are not treated as doc navigation."""

    visible: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    for line in text.splitlines(keepends=True):
        match = FENCE_RE.match(line)
        marker = match.group("marker") if match is not None else ""
        if fence_character is None and marker:
            fence_character = marker[0]
            fence_length = len(marker)
            visible.append("\n" if line.endswith("\n") else "")
            continue
        if (
            fence_character is not None
            and marker
            and marker[0] == fence_character
            and len(marker) >= fence_length
        ):
            fence_character = None
            fence_length = 0
            visible.append("\n" if line.endswith("\n") else "")
            continue
        visible.append(
            ("\n" if line.endswith("\n") else "")
            if fence_character is not None
            else line
        )
    return "".join(visible)


def _heading_slug(value: str) -> str:
    value = re.sub(r"!?(?:\[([^\]]*)\])\([^)]*\)", r"\1", value)
    value = re.sub(r"<[^>]+>", "", value)
    value = value.replace("`", "").replace("*", "").replace("~", "")
    value = "".join(
        character
        for character in value.casefold()
        if character.isalnum() or character in {" ", "\t", "-", "_"}
    )
    return re.sub(r"[ \t]+", "-", value.strip())


def _heading_anchors(text: str) -> set[str]:
    anchors: set[str] = set()
    occurrences: dict[str, int] = {}
    visible = _without_fenced_examples(text)
    for line in visible.splitlines():
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if match is None:
            continue
        base = _heading_slug(match.group(1))
        if not base:
            continue
        index = occurrences.get(base, 0)
        occurrences[base] = index + 1
        anchors.add(base if index == 0 else f"{base}-{index}")
    return anchors


def _resolved_local_links(root: Path, path: Path) -> set[str]:
    targets: set[str] = set()
    text = _without_fenced_examples(path.read_text(encoding="utf-8"))
    for match in LINK_RE.finditer(text):
        raw = match.group(1).strip()
        if not raw or raw.startswith(("#", "http://", "https://", "mailto:")):
            continue
        target_value = unquote(raw.split("#", 1)[0]).strip("<>")
        if not target_value:
            continue
        target = (path.parent / target_value).resolve()
        try:
            targets.add(target.relative_to(root.resolve()).as_posix())
        except ValueError:
            continue
    return targets


def _local_link_errors(root: Path, path: Path) -> list[str]:
    errors: list[str] = []
    text = _without_fenced_examples(path.read_text(encoding="utf-8"))
    for match in LINK_RE.finditer(text):
        raw = match.group(1).strip()
        if not raw or raw.startswith(("http://", "https://", "mailto:")):
            continue
        target_raw, separator, fragment_raw = raw.partition("#")
        target_value = unquote(target_raw).strip("<>")
        fragment = unquote(fragment_raw).casefold()
        target = path if not target_value else (path.parent / target_value).resolve()
        try:
            target.relative_to(root.resolve())
        except ValueError:
            errors.append(f"{path.relative_to(root)}: link escapes repository: {raw}")
            continue
        if not target.exists():
            errors.append(f"{path.relative_to(root)}: missing local link: {raw}")
            continue
        if separator and fragment:
            if not target.is_file() or target.suffix.casefold() != ".md":
                errors.append(
                    f"{path.relative_to(root)}: anchor targets non-Markdown file: {raw}"
                )
                continue
            if fragment not in _heading_anchors(target.read_text(encoding="utf-8")):
                errors.append(
                    f"{path.relative_to(root)}: missing local heading anchor: {raw}"
                )
    return errors


def _navigation_errors(root: Path) -> list[str]:
    errors: list[str] = []
    for relative, required in REQUIRED_NAVIGATION.items():
        path = root / relative
        if not path.is_file():
            continue
        targets = _resolved_local_links(root, path)
        for expected in required:
            if expected not in targets:
                errors.append(f"{relative}: missing required navigation link to {expected}")
    return errors


def _command_target_errors(root: Path, path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    for command_path in COMMAND_TARGET_RE.findall(text):
        if not (root / command_path).is_file():
            errors.append(f"{path.relative_to(root)}: command references missing {command_path}")
    return errors


def _generated_document_ownership_errors(root: Path) -> list[str]:
    """Require source-owned generated Markdown to identify an executable producer."""

    errors: list[str] = []
    owner_pattern = re.compile(
        r"_Generated by `python3 (?P<producer>scripts/[A-Za-z0-9_.-]+\.py)\b[^`]*`\. "
        r"Do not edit by hand\._"
    )
    generated_docs = tuple(
        relative
        for relative in AUTHORITATIVE_BUILD_INPUT_EXCLUDED_PATHS
        if relative.startswith("docs/") and relative.endswith(".md")
    )
    for relative in generated_docs:
        path = root / relative
        if not path.is_file():
            continue
        matches = tuple(owner_pattern.finditer(path.read_text(encoding="utf-8")))
        if len(matches) != 1:
            errors.append(f"{relative}: generated document must declare one owning producer")
            continue
        producer = matches[0].group("producer")
        if not (root / producer).is_file():
            errors.append(f"{relative}: generated document producer is missing: {producer}")
    return errors


def _current_term_errors(root: Path, path: Path) -> list[str]:
    relative = path.relative_to(root).as_posix()
    if relative in HISTORICAL_TERM_DOCS:
        return []
    folded = path.read_text(encoding="utf-8").casefold()
    return [
        f"{relative}: forbidden current terminology {term}"
        for term in FORBIDDEN_CURRENT_TERMS
        if term in folded
    ]


def _runtime_surface_errors(root: Path) -> list[str]:
    """Reject public Runtime choice surfaces while permitting legacy migration prose."""

    errors: list[str] = []
    paths = {
        *_markdown_files(root),
        *(root / relative for relative in RUNTIME_SURFACE_FILES),
    }
    for path in sorted(path for path in paths if path.is_file()):
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        for flag in RETIRED_RUNTIME_FLAGS:
            if flag in text:
                errors.append(f"{relative}: removed Runtime flag remains: {flag}")
        if relative == "pyproject.toml" and "[tool.changeforge.profiles]" in text:
            errors.append(
                "pyproject.toml: retired Runtime Profile metadata table remains"
            )
        if relative in RUNTIME_PROFILE_CHOICE_HISTORY_DOCS:
            continue
        for pattern in RUNTIME_PROFILE_CHOICE_PATTERNS:
            if pattern.search(text):
                errors.append(
                    f"{relative}: retired user-facing Runtime Profile choice remains"
                )
                break
    return errors


def _mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationProblem(f"{context} must be a mapping")
    return value


def _list(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationProblem(f"{context} must be a list")
    return value


def _registry_authority(root: Path) -> dict[str, Any]:
    registries: dict[str, list[dict[str, Any]]] = {}
    for layer, (relative, field) in REGISTRY_SPECS.items():
        document = _mapping(load_yaml_file(root / relative), relative)
        entries = _list(document.get(field), f"{relative}:{field}")
        registries[layer] = [
            _mapping(entry, f"{relative}:{field}[{index}]")
            for index, entry in enumerate(entries)
        ]

    counts = {layer: len(entries) for layer, entries in registries.items()}
    total = sum(counts.values())
    non_control = total - counts["control"]
    runtime_top_level_count = counts["control"] + counts["professional"]
    if runtime_top_level_count != RUNTIME_SKILL_COUNT:
        raise ValidationProblem(
            "registry Runtime top-level count does not match installer authority"
        )
    return {
        "registries": registries,
        "counts": counts,
        "total": total,
        "non_control": non_control,
        "runtime_top_level_count": runtime_top_level_count,
    }


def _canonical_reference_content(root: Path) -> dict[str, Any]:
    """Collect Reference facts through the repository's canonical collector."""

    collector_path = SCRIPT_DIR / "audit-skill-content.py"
    module_name = (
        "_changeforge_docs_reference_collector_"
        + hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()[:16]
    )
    spec = importlib.util.spec_from_file_location(module_name, collector_path)
    if spec is None or spec.loader is None:
        raise ValidationProblem(
            f"cannot load canonical Reference collector {collector_path}"
        )
    module = importlib.util.module_from_spec(spec)
    previous_module = sys.modules.get(module_name)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        module.ROOT = root
        module.CONTROL_SKILLS_DIR = root / "src/control-skills"
        module.PROFESSIONAL_SKILLS_DIR = root / "src/professional-skills"
        module.CAPABILITIES_DIR = root / "src/foundation/capabilities"
        module.DOMAIN_EXTENSIONS_DIR = root / "src/domain-extensions"
        module.CONTROL_REGISTRY = root / "src/registry/control-skills.yaml"
        module.PROFESSIONAL_REGISTRY = root / "src/registry/professional-skills.yaml"
        module.CAPABILITIES_REGISTRY = root / "src/registry/foundation-skills.yaml"
        module.DOMAIN_REGISTRY = root / "src/registry/domain-skills.yaml"
        module.SKILL_CONTENT_EXCEPTIONS_FILE = (
            root / "config/skill-content-exceptions.yaml"
        )
        module.REFERENCE_SOURCES = (
            (
                "control",
                module.CONTROL_REGISTRY,
                "control_skills",
                module.CONTROL_SKILLS_DIR,
            ),
            (
                "professional",
                module.PROFESSIONAL_REGISTRY,
                "professional_skills",
                module.PROFESSIONAL_SKILLS_DIR,
            ),
            (
                "foundation",
                module.CAPABILITIES_REGISTRY,
                "foundation_skills",
                module.CAPABILITIES_DIR,
            ),
            (
                "domain",
                module.DOMAIN_REGISTRY,
                "domain_skills",
                module.DOMAIN_EXTENSIONS_DIR,
            ),
        )
        module.REFERENCE_LAYER_ORDER = {
            layer: index
            for index, (layer, _registry, _key, _skills_root) in enumerate(
                module.REFERENCE_SOURCES
            )
        }
        collected = module._collect_reference_content()
    except Exception as exc:
        raise ValidationProblem(
            f"canonical Reference inventory collector failed: {exc}"
        ) from exc
    finally:
        if previous_module is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = previous_module
    return _mapping(collected, "canonical Reference inventory")


def _reference_inventory_authority(root: Path) -> dict[str, int]:
    try:
        collected = _canonical_reference_content(root)
    except ValidationProblem:
        raise
    except Exception as exc:
        raise ValidationProblem(
            f"canonical Reference inventory collector failed: {exc}"
        ) from exc
    summary = _mapping(
        collected.get("summary"),
        "canonical Reference inventory summary",
    )

    def count(field: str) -> int:
        value = summary.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValidationProblem(
                f"canonical Reference inventory summary.{field} "
                "must be a non-negative integer"
            )
        return value

    indexed_entries = count("indexed_reference_entries")
    indexed_paths = count("indexed_unique_paths")
    existing_indexed = count("existing_indexed_references")
    physical = count("physical_markdown_references")
    missing = count("missing_references")
    orphans = count("orphan_references")
    unindexed_templates = count("unindexed_template_assets")
    preface_errors = count("effective_preface_contract_errors")

    if indexed_entries != indexed_paths or indexed_entries != existing_indexed:
        raise ValidationProblem(
            "canonical Reference inventory must have equal indexed-entry, "
            "unique-path, and existing-indexed counts"
        )
    if missing or orphans or preface_errors:
        raise ValidationProblem(
            "canonical Reference inventory contains missing, orphan, or "
            "effective-preface contract errors"
        )
    if physical != existing_indexed + unindexed_templates:
        raise ValidationProblem(
            "canonical Reference inventory physical count must equal existing "
            "indexed References plus unindexed template assets"
        )
    return {
        "indexed": indexed_entries,
        "physical": physical,
        "unindexed_templates": unindexed_templates,
    }


def _volatile_fact_authority(root: Path) -> dict[str, Any]:
    """Derive volatile documentation facts from their owning source files."""

    registry = _registry_authority(root)
    registries = registry["registries"]
    counts = registry["counts"]
    foundation_delivery = Counter(
        str(entry.get("delivery_scope") or "")
        for entry in registries["foundation"]
    )
    routing_only = (
        foundation_delivery["dev-only"] + foundation_delivery["authoring-only"]
    )
    runtime_delivery = {
        "targeted": foundation_delivery["product"] + counts["domain"],
        "routing_only": routing_only,
    }

    foundation_names = {str(entry.get("name")) for entry in registries["foundation"]}
    layer3_candidates = {
        str(candidate)
        for entry in registries["professional"]
        for candidate in _list(
            entry.get("layer3_candidates", []),
            f"professional:{entry.get('name')}:layer3_candidates",
        )
    }

    routing_cases = _list(
        _mapping(
            load_yaml_file(root / "evals/routing/cases.yaml"),
            "evals/routing/cases.yaml",
        ).get("cases"),
        "evals/routing/cases.yaml:cases",
    )
    capability_cases = _list(
        _mapping(
            load_yaml_file(root / "evals/routing/capability-coverage-cases.yaml"),
            "evals/routing/capability-coverage-cases.yaml",
        ).get("cases"),
        "evals/routing/capability-coverage-cases.yaml:cases",
    )
    admission_cases = _list(
        _mapping(
            load_yaml_file(root / "evals/capability-coverage/admission-cases.yaml"),
            "evals/capability-coverage/admission-cases.yaml",
        ).get("cases"),
        "evals/capability-coverage/admission-cases.yaml:cases",
    )
    admission_counts = Counter(
        str(_mapping(case, "admission case").get("layer"))
        for case in admission_cases
    )
    matrix_entries = _list(
        _mapping(
            load_yaml_file(root / "evals/capability-coverage/matrix.yaml"),
            "evals/capability-coverage/matrix.yaml",
        ).get("entries"),
        "evals/capability-coverage/matrix.yaml:entries",
    )
    coverage_counts = Counter(
        str(_mapping(entry, "capability matrix entry").get("coverage_status"))
        for entry in matrix_entries
    )

    return {
        "counts": counts,
        "total": registry["total"],
        "non_control": registry["non_control"],
        "runtime_top_level_count": registry["runtime_top_level_count"],
        "runtime_delivery": runtime_delivery,
        "routing_case_count": len(routing_cases),
        "capability_routing_case_count": len(capability_cases),
        "admission_case_count": len(admission_cases),
        "admission_counts": admission_counts,
        "foundation_candidate_count": len(layer3_candidates & foundation_names),
        "layer3_catalog_count": counts["foundation"] + counts["domain"],
        "matrix_entry_count": len(matrix_entries),
        "coverage_counts": coverage_counts,
        "reference_inventory": _reference_inventory_authority(root),
    }


def _required_volatile_projections(authority: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    counts = authority["counts"]
    runtime_top_level = authority["runtime_top_level_count"]
    delivery = authority["runtime_delivery"]
    admissions = authority["admission_counts"]
    coverage = authority["coverage_counts"]
    references = authority["reference_inventory"]
    inventory = (
        f"1 Control, {counts['professional']} Professional, "
        f"{counts['foundation']} Foundation, and {counts['domain']} Domain Skills: "
        f"{authority['total']} total and {authority['non_control']} non-Control"
    )
    runtime_count = f"{runtime_top_level} top-level Skills"
    delivery_counts = (
        f"{runtime_top_level}/{delivery['targeted']}/"
        f"{delivery['routing_only']} top-level/targeted/routing-only"
    )
    routing = (
        f"{authority['routing_case_count']} canonical entries and "
        f"{authority['capability_routing_case_count']} capability entries"
    )
    admission = (
        f"{authority['admission_case_count']} admissions are "
        f"{admissions['professional']} Professional, "
        f"{admissions['foundation']} Foundation, and {admissions['domain']} Domain"
    )
    layer3 = (
        f"{authority['foundation_candidate_count']} unique Foundation Skills in the "
        f"{authority['layer3_catalog_count']}-entry Layer 3 catalog"
    )
    matrix = (
        f"{authority['matrix_entry_count']} entries classify as "
        f"{coverage['covered']} covered, {coverage['partial']} partial, "
        f"{coverage['missing']} missing, and "
        f"{coverage['intentionally-unsupported']} intentionally unsupported"
    )
    reference_inventory = (
        f"{references['indexed']} registry-indexed Markdown files and "
        f"{references['physical']} physical Markdown files"
    )
    unindexed_templates = (
        f"Exactly {references['unindexed_templates']} physical Reference "
        f"{'is' if references['unindexed_templates'] == 1 else 'are'} unindexed"
    )
    return {
        "AGENTS.md": (inventory, runtime_count, delivery_counts),
        ".github/pull_request_template.md": (
            f"all {authority['non_control']} effective packages are accepted",
            f"{authority['non_control']}/{authority['non_control']} effective coverage",
        ),
        "CHANGELOG.md": (routing, layer3, matrix),
        "docs/BUILD_PROFILES.md": (
            inventory,
            runtime_count,
            delivery_counts,
            reference_inventory,
            unindexed_templates,
        ),
        "docs/VALIDATION.md": (routing, admission, layer3, matrix, runtime_count),
        "docs/SCORECARD.md": (inventory, routing, admission, layer3, matrix, delivery_counts),
        "docs/BENCHMARKS.md": (f"all {counts['domain']} Domain Skills",),
        "src/foundation/capabilities/README.md": (
            f"contains {counts['foundation']} implemented Foundation Skills plus "
            "`_template`",
        ),
    }


def _current_projection_text(relative: str, text: str) -> str:
    if relative != "CHANGELOG.md":
        return text
    match = re.search(
        r"^## Unreleased\s*$.*?(?=^##\s|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise ValidationProblem("CHANGELOG.md must contain an Unreleased section")
    return match.group(0)


def _volatile_fact_errors(root: Path) -> list[str]:
    errors: list[str] = []
    try:
        authority = _volatile_fact_authority(root)
    except (OSError, ValidationProblem, KeyError, TypeError, ValueError) as exc:
        return [f"volatile documentation authority is invalid: {exc}"]

    for relative, projections in _required_volatile_projections(authority).items():
        path = root / relative
        if not path.is_file():
            continue
        try:
            current_text = _current_projection_text(
                relative,
                path.read_text(encoding="utf-8"),
            )
        except (OSError, ValidationProblem) as exc:
            errors.append(f"{relative}: cannot validate current facts: {exc}")
            continue
        normalized = _normalized_document_text(current_text)
        for projection in projections:
            if _normalized_document_text(projection) not in normalized:
                errors.append(
                    f"{relative}: missing authority-derived current fact {projection!r}"
                )

    domain_count = authority["counts"]["domain"]
    word_counts = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
    }
    domain_pattern = re.compile(
        r"\ball\s+(?P<count>\d+|one|two|three|four|five|six|seven|eight|"
        r"nine|ten|eleven|twelve|thirteen)\s+Domain Skills\b",
        re.IGNORECASE,
    )
    for relative in VOLATILE_FACT_DOCS:
        path = root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for match in domain_pattern.finditer(text):
            raw = match.group("count").casefold()
            actual = int(raw) if raw.isdigit() else word_counts[raw]
            if actual != domain_count:
                errors.append(
                    f"{relative}: stale Domain Skill count {actual}; "
                    f"registry authority reports {domain_count}"
                )
    return errors


def _current_evidence_authority(root: Path) -> dict[str, Any]:
    registry = _registry_authority(root)
    exceptions = _mapping(
        load_yaml_file(root / "config/skill-content-exceptions.yaml"),
        "config/skill-content-exceptions.yaml",
    )
    root_dispositions = _mapping(
        exceptions.get("root_semantic_dispositions"),
        "root_semantic_dispositions",
    )
    if root_dispositions.get("schema_version") != 8 or "lifecycle" in (
        root_dispositions
    ):
        raise ValidationProblem(
            "root_semantic_dispositions must use lifecycle-free stable-selector schema 8"
        )
    reference_dispositions = _mapping(
        exceptions.get("reference_semantic_dispositions"),
        "reference_semantic_dispositions",
    )
    if reference_dispositions.get("schema_version") != 3:
        raise ValidationProblem(
            "reference_semantic_dispositions must use stable-selector schema 3"
        )
    legacy_evidence = _mapping(
        exceptions.get("semantic_disposition_legacy_evidence"),
        "semantic_disposition_legacy_evidence",
    )
    if legacy_evidence.get("schema_version") != 1:
        raise ValidationProblem(
            "semantic_disposition_legacy_evidence must use immutable schema 1"
        )
    review_config = _mapping(
        load_yaml_file(root / "config/professionalism-release-review.yaml"),
        "config/professionalism-release-review.yaml",
    )
    readability = _mapping(
        review_config.get("readability_review_attestation"),
        "readability_review_attestation",
    )
    professional = _mapping(
        review_config.get("professional_completeness_review_attestation"),
        "professional_completeness_review_attestation",
    )
    selector_free_fields = {
        "schema_version",
        "panel_kind",
        "scope",
        "decision_method",
        "limitations",
    }
    for label, axis_config in (
        ("readability_review_attestation", readability),
        ("professional_completeness_review_attestation", professional),
    ):
        if set(axis_config) != selector_free_fields:
            raise ValidationProblem(
                f"{label} must use the selector-free schema 5 config contract"
            )
    stable_identity = {
        "readability": (
            readability.get("schema_version"),
            readability.get("panel_kind"),
            readability.get("scope"),
        ),
        "professional-completeness": (
            professional.get("schema_version"),
            professional.get("panel_kind"),
            professional.get("scope"),
        ),
    }
    expected_stable_identity = {
        "readability": (5, "readability", "ai-readability-and-density"),
        "professional-completeness": (
            5,
            "professional-completeness",
            "professional-skill-packages",
        ),
    }
    if stable_identity != expected_stable_identity:
        raise ValidationProblem("expert evidence authority identity is not canonical")

    fixed_paths = {
        "readability": "evals/expert-panel/readability.json",
        "semantic-disposition": "evals/expert-panel/semantic-disposition.json",
        "professional-completeness": (
            "evals/expert-panel/professional-completeness.json"
        ),
    }
    return {
        "non_control": registry["non_control"],
        "canonical_fixed_paths": True,
        "migration_state": "current",
        "fixed_paths": fixed_paths,
    }


def _current_evidence_projection(authority: dict[str, Any]) -> str:
    return (
        "Canonical fixed-attestation paths, not Readability or Professional "
        "policy config, select Expert Panel evidence; the formal target "
        f"remains all {authority['non_control']} non-Control packages."
    )


def _configured_provider_proof_limit(root: Path) -> str:
    review_config = _mapping(
        load_yaml_file(root / "config/professionalism-release-review.yaml"),
        "config/professionalism-release-review.yaml",
    )
    configured_clauses: list[str] = []
    for attestation_name in (
        "readability_review_attestation",
        "professional_completeness_review_attestation",
    ):
        attestation = _mapping(
            review_config.get(attestation_name),
            attestation_name,
        )
        limitations = _list(
            attestation.get("limitations"),
            f"{attestation_name}.limitations",
        )
        clauses = [
            clause.strip().rstrip(".")
            for limitation in limitations
            if isinstance(limitation, str)
            for clause in re.split(r",\s*|\s+or\s+", limitation)
            if "provider" in clause.casefold()
        ]
        if len(clauses) != 1:
            raise ValidationProblem(
                f"{attestation_name}.limitations must define one provider proof limit"
            )
        configured_clauses.append(clauses[0])
    if len(set(configured_clauses)) != 1:
        raise ValidationProblem(
            "readability and professional completeness provider proof limits differ"
        )
    return configured_clauses[0]


def _current_evidence_projection_errors(root: Path) -> list[str]:
    try:
        authority = _current_evidence_authority(root)
        provider_proof_limit = _configured_provider_proof_limit(root)
    except (OSError, ValidationProblem, KeyError, TypeError, ValueError) as exc:
        return [f"current evidence authority is invalid: {exc}"]
    expected = _normalized_document_text(_current_evidence_projection(authority))
    expected_inventory = tuple(
        _normalized_document_text(f"`evals/expert-panel/{name}.json`")
        for name in (
            "readability",
            "semantic-disposition",
            "professional-completeness",
        )
    )
    expected_runtime = _normalized_document_text(
        "`.rd-skills/expert-panel/<run-id>/`"
    )
    boundary = _normalized_document_text(
        "These fixed attestations do not prove that the final local formal gate "
        "passed."
    )
    errors: list[str] = []
    for relative in CURRENT_EVIDENCE_DOCS:
        path = root / relative
        if not path.is_file():
            continue
        normalized = _normalized_document_text(path.read_text(encoding="utf-8"))
        if expected not in normalized:
            errors.append(
                f"{relative}: current fixed evidence does not match authoritative configs"
            )
        if any(item not in normalized for item in expected_inventory):
            errors.append(
                f"{relative}: missing exact compact expert-panel inventory"
            )
        if expected_runtime not in normalized:
            errors.append(f"{relative}: missing ignored expert-panel runtime root")
        if boundary not in normalized:
            errors.append(
                f"{relative}: current static evidence must retain the formal-gate proof limit"
            )
    expected_provider_limit = _normalized_document_text(provider_proof_limit)
    for relative in STATIC_EVIDENCE_PROOF_LIMIT_DOCS:
        path = root / relative
        if not path.is_file():
            continue
        normalized = _normalized_document_text(path.read_text(encoding="utf-8"))
        if expected_provider_limit not in normalized:
            errors.append(
                f"{relative}: static evidence proof limit must include "
                f"{provider_proof_limit} from the review config"
            )
    return errors


def _markdown_tables(text: str) -> tuple[tuple[tuple[str, ...], ...], ...]:
    tables: list[tuple[tuple[str, ...], ...]] = []
    current: list[tuple[str, ...]] = []
    for line in (*text.splitlines(), ""):
        if line.startswith("|"):
            cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
            if cells and not all(re.fullmatch(r":?-+:?", cell) for cell in cells):
                current.append(cells)
            continue
        if current:
            tables.append(tuple(current))
            current = []
    return tuple(tables)


def _host_product_table_rows(
    text: str,
    expected_labels: set[str],
) -> tuple[tuple[str, ...], ...]:
    candidates = []
    for table in _markdown_tables(text):
        data = table[1:]
        matched = len({row[0] for row in data if row} & expected_labels)
        candidates.append((matched, data))
    if not candidates:
        return ()
    matched, rows = max(candidates, key=lambda item: item[0])
    return rows if matched else ()


def _expected_host_product_rows(root: Path) -> tuple[tuple[str, ...], ...]:
    contract = read_host_product_surfaces(
        root / HOST_PRODUCT_SURFACES_SOURCE
    )["surfaces"]
    delivery_labels = {
        "skills-and-agent-profiles": "Skills + Agent Profiles",
        "skills-only": "Skills only",
        "zip-packages": "Zip packages",
    }
    live_labels = {
        "not-established": "Not established",
        "not-applicable": "Not applicable",
    }
    workflow_labels = {
        "available": "Available",
        "not-established": "Not established",
        "integration-owned": "API integration owns orchestration",
    }
    limitation_labels = {
        "artifact-health-only": "Artifacts checked; live loading not proved",
        "copilot-cli-only": "Copilot CLI only",
        "artifact-delivery-only": "Artifact delivery only",
        "api-integration-only": "API integration only",
    }
    rows: list[tuple[str, ...]] = []
    for agent in INSTALLER_AGENTS:
        surface = contract[agent]
        live = (
            f"`{surface['invocation']}`"
            if surface["live_skill_invocation"] == "supported"
            else live_labels[surface["live_skill_invocation"]]
        )
        rows.append(
            (
                surface["label"],
                delivery_labels[surface["artifact_delivery"]],
                live,
                workflow_labels[surface["full_workflow"]],
                limitation_labels[surface["limitation_code"]],
            )
        )
    return tuple(rows)


def _task_example_invocation_tokens(text: str) -> tuple[str, ...]:
    """Return only invocation tokens that open runnable text task examples."""

    tokens: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    language = ""
    body: list[str] = []
    invocation = re.compile(r"^[$/][a-z0-9]+(?:-[a-z0-9]+)*$")
    for line in text.splitlines():
        marker_match = FENCE_RE.match(line)
        marker = marker_match.group("marker") if marker_match is not None else ""
        if fence_character is None:
            if marker:
                fence_character = marker[0]
                fence_length = len(marker)
                language = line[marker_match.end() :].strip().casefold()
                body = []
            continue
        if (
            marker
            and marker[0] == fence_character
            and len(marker) >= fence_length
        ):
            if language == "text":
                first = next(
                    (index for index, value in enumerate(body) if value.strip()),
                    None,
                )
                if (
                    first is not None
                    and invocation.fullmatch(body[first].strip())
                    and first + 1 < len(body)
                    and not body[first + 1].strip()
                    and any(value.strip() for value in body[first + 2 :])
                ):
                    tokens.append(body[first].strip())
            fence_character = None
            fence_length = 0
            language = ""
            body = []
            continue
        body.append(line)
    return tuple(tokens)


def _host_product_surface_errors(root: Path) -> list[str]:
    """Validate structured Host facts without freezing surrounding product copy."""

    errors: list[str] = []
    try:
        expected = _expected_host_product_rows(root)
    except (InstallError, KeyError, TypeError) as exc:
        return [f"{HOST_PRODUCT_SURFACES_SOURCE}: {exc}"]

    expected_labels = {row[0] for row in expected}
    for relative in ("README.md", "docs/QUICKSTART.md"):
        path = root / relative
        if not path.is_file():
            continue
        actual = _host_product_table_rows(
            path.read_text(encoding="utf-8"),
            expected_labels,
        )
        factual = tuple(row[:5] for row in actual)
        if factual != expected:
            errors.append(
                f"{relative}: Host delivery/invocation/workflow table must match "
                f"{HOST_PRODUCT_SURFACES_SOURCE}"
            )

    texts = {
        relative: (root / relative).read_text(encoding="utf-8")
        for relative in HOST_INVOCATION_ONBOARDING_DOCS
        if (root / relative).is_file()
    }
    universal_slash = re.compile(
        r"\b(?:all\s+(?:supported\s+)?hosts?|every\s+host)\s+"
        r"(?:use|uses|start|starts|invoke|invokes)[^\n]*"
        r"/engineering-control-plane",
        re.IGNORECASE,
    )
    unsupported_claims = (
        re.compile(
            r"(?mi)^(?:.*\bCline\b.{0,100}full rd-skills workflow (?:is )?available|"
            r".*full rd-skills workflow (?:is )?available.{0,100}\bCline\b).*$"
        ),
        re.compile(
            r"(?mi)^(?:.*\bOpenAI API\b.{0,100}live (?:Skill|Host) "
            r"(?:invocation|installation) (?:is )?supported|.*live (?:Skill|Host) "
            r"(?:invocation|installation) (?:is )?supported.{0,100}\bOpenAI API\b).*$"
        ),
        re.compile(
            r"(?mi)^.*(?:every|all|other) (?:GitHub )?Copilot surfaces?.*"
            r"(?:use|support|available).*(?:/engineering-control-plane|full workflow).*$"
        ),
        re.compile(
            r"(?mi)^.*available.{0,80}(?:every|all) (?:GitHub )?Copilot surfaces?.*$"
        ),
    )
    for relative, text in texts.items():
        contract = read_host_product_surfaces(
            root / HOST_PRODUCT_SURFACES_SOURCE
        )["surfaces"]
        expected_codex = contract["codex"]["invocation"]
        for token in _task_example_invocation_tokens(text):
            if token != expected_codex:
                errors.append(
                    f"{relative}: invocation token {token} conflicts with "
                    f"{HOST_PRODUCT_SURFACES_SOURCE}"
                )
        if universal_slash.search(text):
            errors.append(f"{relative}: universal Slash invocation claim is unsupported")
        if any(pattern.search(text) for pattern in unsupported_claims):
            errors.append(f"{relative}: unsupported Host workflow claim")
    return errors


def _product_surface_errors(root: Path) -> list[str]:
    errors: list[str] = []
    readme = root / "README.md"
    if readme.is_file():
        text = readme.read_text(encoding="utf-8")
        level_two_headings = tuple(re.finditer(r"(?m)^##\s+", text))
        first_surface_end = (
            level_two_headings[1].start()
            if len(level_two_headings) > 1
            else len(text)
        )
        first_surface = text[:first_surface_end]
        normalized = first_surface.casefold()
        for term in README_FIRST_SURFACE_FORBIDDEN:
            if term in normalized:
                errors.append(
                    f"README.md: first product surface exposes internal term {term}"
                )

    quickstart = root / "docs/QUICKSTART.md"
    if quickstart.is_file():
        text = quickstart.read_text(encoding="utf-8")
        normalized = text.casefold()
        for term in ("runtime", *BEGINNER_PROTOCOL_TUTORIAL_TERMS):
            if term in normalized:
                errors.append(
                    f"docs/QUICKSTART.md: beginner path teaches internal term {term}"
                )

    usage = root / "docs/USAGE.md"
    if usage.is_file():
        normalized = usage.read_text(encoding="utf-8").casefold()
        for term in BEGINNER_PROTOCOL_TUTORIAL_TERMS:
            if term in normalized:
                errors.append(
                    f"docs/USAGE.md: daily-use guide teaches internal term {term}"
                )

    if (root / "docs/ROUTING_EXAMPLES.md").exists():
        errors.append(
            "docs/ROUTING_EXAMPLES.md: scenarios must be owned by docs/USAGE.md"
        )
    return errors


def _shell_fence_placeholder_errors(root: Path, path: Path) -> list[str]:
    errors: list[str] = []
    language: str | None = None
    start_line = 0
    body: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        marker = FENCE_RE.match(line)
        if marker is not None:
            if language is None:
                language = line[len(marker.group("marker")) :].strip().casefold()
                start_line = line_number
                body = []
            else:
                if language in SHELL_FENCE_LANGUAGES and SHELL_PLACEHOLDER_RE.search(
                    "\n".join(body)
                ):
                    errors.append(
                        f"{path.relative_to(root)}:{start_line}: shell fence contains "
                        "non-executable placeholder syntax; use a text usage block"
                    )
                language = None
                body = []
            continue
        if language is not None:
            body.append(line)
    return errors


def _release_process_errors(root: Path) -> list[str]:
    path = root / "docs/RELEASE.md"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    required = (
        "Check the four selected evidence surfaces before creating review artifacts.",
        "If all four surfaces are current, create no expert panel.",
        "Refresh only the stale surface.",
        "An all-carry Professional Completeness round creates no fresh reviewer artifacts: zero fresh reviewers, ballots, capsules, and input bytes.",
    )
    normalized = _normalized_document_text(text)
    errors = [
        f"docs/RELEASE.md: missing selective evidence rule {phrase}"
        for phrase in required
        if _normalized_document_text(phrase) not in normalized
    ]
    if re.search(
        r"(?im)^\s*(?:\d+\.\s*)?(?:\*\*)?Produce independent expert evidence\b",
        text,
    ):
        errors.append(
            "docs/RELEASE.md: release sequence still unconditionally produces expert panels"
        )
    conditional = text.find("## Conditional Evidence Refresh")
    first_prepare = text.find("expert_panel_review.py prepare")
    if first_prepare >= 0 and (conditional < 0 or first_prepare < conditional):
        errors.append(
            "docs/RELEASE.md: prepare commands must appear only under conditional refresh"
        )
    return errors


def _governance_context_budget_authority_block(
    core_contracts: dict[str, object],
) -> str:
    contract = core_contracts["context_budget_contract"]
    rows = [
        f"| {row['label']} | {row['soft_target']} | {row['hard_ceiling']} |"
        for row in contract["budget_classes"].values()
    ]
    return "\n".join(
        [
            GOVERNANCE_BUDGET_BEGIN,
            "## Rendered Context Budget Authority",
            "",
            f"[{GOVERNANCE_BUDGET_REPORT}]({GOVERNANCE_BUDGET_REPORT}) is",
            "the single source of truth for current rendered token totals, maximum fixture",
            "IDs, margins, duplicate-rule ratio, and pass/fail status. Governance records no",
            "current measurement snapshot.",
            "",
            "The provisional migration soft targets and hard ceilings below come from",
            "`src/control-model/core-contracts.json#/context_budget_contract`. They are",
            "guardrails, not current measurements or calibrated optima.",
            "",
            "| Context | Soft target | Hard ceiling |",
            "| --- | ---: | ---: |",
            *rows,
            "",
            "The report must exist, have `status: pass`, report no errors, and project these",
            "limits unchanged. Run `python3 scripts/eval-rendered-context-budget.py --mode conformance` to",
            "refresh current evidence.",
            GOVERNANCE_BUDGET_END,
        ]
    )


def _governance_budget_report_path(reports_dir: Path) -> Path:
    return reports_dir / Path(GOVERNANCE_BUDGET_REPORT).name


def _governance_context_budget_errors(
    root: Path,
    core_contracts: dict[str, object],
    reports_dir: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    governance_path = root / "GOVERNANCE.md"
    if not governance_path.is_file():
        return ["GOVERNANCE.md: missing fixed ceiling authority block"]
    text = governance_path.read_text(encoding="utf-8")
    if (
        text.count(GOVERNANCE_BUDGET_BEGIN) != 1
        or text.count(GOVERNANCE_BUDGET_END) != 1
    ):
        errors.append(
            "GOVERNANCE.md: fixed ceiling authority block markers must appear exactly once"
        )
        outside = text
    else:
        start = text.index(GOVERNANCE_BUDGET_BEGIN)
        end = text.index(GOVERNANCE_BUDGET_END, start) + len(
            GOVERNANCE_BUDGET_END
        )
        actual = text[start:end]
        expected = _governance_context_budget_authority_block(core_contracts)
        if actual != expected:
            errors.append(
                "GOVERNANCE.md: fixed ceiling authority block must equal the "
                "Core-derived rendering"
            )
        outside = text[:start] + text[end:]

    snapshot_patterns = (
        re.compile(r"\b\d{3,5}/\d{3,5}\b"),
        re.compile(r"\b\d{3,5}\s+tokens?\b", re.IGNORECASE),
        re.compile(
            r"\b(?:current|observed|rendered\s+maximum|maxima|margin)\b"
            r"[^\n]{0,100}\b\d{3,5}(?:\.\d+)?\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bduplicate(?:-rule)?(?:\s+token)?\s+ratio\b"
            r"[^\n]{0,80}\b\d+(?:\.\d+)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:soft\s+targets?|hard\s+ceilings?|ceilings?)\b"
            r"[^\n]{0,80}\b\d{3,5}\b",
            re.IGNORECASE,
        ),
    )
    if any(pattern.search(outside) for pattern in snapshot_patterns):
        errors.append(
            "GOVERNANCE.md: must not copy current rendered measurements or "
            "declare budget limits outside the Core-derived authority block"
        )

    report_path = _governance_budget_report_path(
        root / Path(GOVERNANCE_BUDGET_REPORT).parent
        if reports_dir is None
        else reports_dir
    )
    if not report_path.is_file():
        errors.append(
            f"{GOVERNANCE_BUDGET_REPORT}: rendered context budget report is missing"
        )
        return errors
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(
            f"{GOVERNANCE_BUDGET_REPORT}: rendered context budget report is malformed: {exc}"
        )
        return errors
    if not isinstance(report, dict):
        errors.append(
            f"{GOVERNANCE_BUDGET_REPORT}: rendered context budget report must be an object"
        )
        return errors
    if report.get("status") != "pass" or report.get("errors") != []:
        errors.append(
            f"{GOVERNANCE_BUDGET_REPORT}: rendered context budget report must "
            "have status pass and no errors"
        )

    limits = derived_context_budget_limits(core_contracts["context_budget_contract"])
    expected_soft_targets = {
        budget_class: limit["soft_target"]
        for budget_class, limit in limits.items()
    }
    expected_hard_ceilings = {
        budget_class: limit["hard_ceiling"]
        for budget_class, limit in limits.items()
    }
    governance = report.get("budget_governance")
    if (
        not isinstance(governance, dict)
        or governance.get("mode") != "conformance"
        or governance.get("soft_targets") != expected_soft_targets
        or governance.get("hard_ceilings") != expected_hard_ceilings
        or governance.get("conformance_failures") != []
    ):
        errors.append(
            f"{GOVERNANCE_BUDGET_REPORT}: rendered context Conformance limits "
            "or failure state do not match Core"
        )
    aggregate = report.get("aggregate")
    maxima: dict[str, object] = {}
    if isinstance(aggregate, dict):
        maxima["main"] = aggregate.get("max_main")
        by_class = aggregate.get("max_by_budget_class")
        if isinstance(by_class, dict):
            maxima.update(by_class)
    for budget_class, soft_target in expected_soft_targets.items():
        maximum = maxima.get(budget_class)
        if (
            not isinstance(maximum, dict)
            or maximum.get("soft_target") != soft_target
            or maximum.get("hard_ceiling") != expected_hard_ceilings[budget_class]
            or maximum.get("within_hard_ceiling") is not True
        ):
            errors.append(
                f"{GOVERNANCE_BUDGET_REPORT}: rendered context budget report "
                f"maximum for {budget_class!r} does not match Core limits"
            )
    return errors


def _governance_issue_section(text: str, issue_id: str) -> str | None:
    match = re.search(
        rf"(?ms)^### {re.escape(issue_id)}\b.*?(?=^### |\Z)",
        text,
    )
    return match.group(0) if match is not None else None


def _governance_link_targets(text: str) -> set[str]:
    targets: set[str] = set()
    for match in LINK_RE.finditer(_without_fenced_examples(text)):
        raw = match.group(1).strip()
        if not raw or raw.startswith(("#", "http://", "https://", "mailto:")):
            continue
        target = unquote(raw.split("#", 1)[0]).strip("<>")
        if target:
            targets.add(target)
    return targets


def _governance_evidence_freshness_errors(root: Path) -> list[str]:
    path = root / "GOVERNANCE.md"
    if not path.is_file():
        return ["GOVERNANCE.md: missing current-evidence authority"]
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    historical_block = re.compile(
        r"(?ms)^- \*\*Historical, non-current resolution evidence:\*\*"
        r".*?(?=^- \*\*|\Z)"
    )
    current_evidence = historical_block.sub("", text)
    for pattern in GOVERNANCE_VOLATILE_EVIDENCE_PATTERNS:
        if pattern.search(current_evidence):
            errors.append(
                "GOVERNANCE.md: volatile current evidence snapshot must be replaced "
                "with its authoritative source, test module, or report link"
            )

    for issue_id, required_targets in GOVERNANCE_EVIDENCE_AUTHORITIES.items():
        section = _governance_issue_section(text, issue_id)
        if section is None:
            errors.append(f"GOVERNANCE.md: missing {issue_id} evidence section")
            continue
        targets = _governance_link_targets(section)
        for target in required_targets:
            if target not in targets:
                errors.append(
                    f"GOVERNANCE.md: {issue_id} must link current-evidence authority "
                    f"{target}"
                )

    rds_010 = _governance_issue_section(text, "RDS-010")
    if rds_010 is not None:
        if GOVERNANCE_HISTORICAL_EVIDENCE_LABEL not in rds_010:
            errors.append(
                "GOVERNANCE.md: RDS-010 digest evidence must be explicitly labeled "
                "historical, non-current"
            )
        historical_rds_010 = historical_block.search(rds_010)
        digest_matches = tuple(
            re.finditer(r"\b[0-9a-f]{64}\b", rds_010, re.IGNORECASE)
        )
        if any(
            historical_rds_010 is None
            or not historical_rds_010.start() <= digest.start() < historical_rds_010.end()
            for digest in digest_matches
        ):
            errors.append(
                "GOVERNANCE.md: RDS-010 digest evidence must remain inside the "
                "historical, non-current evidence block"
            )
        normalized = _normalized_document_text(rds_010)
        if (
            ".changeforge-build-manifest.json" not in rds_010
            or "single source of truth" not in normalized
        ):
            errors.append(
                "GOVERNANCE.md: RDS-010 must identify current generated manifests "
                "and the linked installation report as freshness authorities"
            )
    return errors


def _normalized_document_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def _layer3_cardinality_guidance_errors(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in LAYER3_CARDINALITY_GUIDANCE_FILES:
        path = root / relative
        if not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8")
        normalized = _normalized_document_text(raw)
        if any(
            _normalized_document_text(fact) not in normalized
            for fact in LAYER3_CARDINALITY_GUIDANCE_FACTS
        ):
            errors.append(
                f"{relative}: Layer 3 cardinality guidance must state the exact "
                "ordered-unique zero-to-three, fail-closed, never-truncate contract"
            )
        if any(pattern.search(raw) for pattern in SOFTENED_LAYER3_CARDINALITY_PATTERNS):
            errors.append(
                f"{relative}: Layer 3 cardinality guidance must not permit "
                "risk-based exceptions to the hard maximum"
            )
    return errors


def _document_path(path: Path) -> str:
    try:
        relative = path.relative_to(Path.home())
    except ValueError:
        return path.as_posix()
    return "~" if not relative.parts else f"~/{relative.as_posix()}"


def _installer_agent_label(agent: str) -> str:
    return "OpenAI API" if agent == "openai-api" else agent.title()


def _expected_installation_matrix_rows() -> tuple[str, ...]:
    """Project installer authority into the human-facing installation matrix."""

    rows: list[str] = []
    for agent in INSTALLER_AGENTS:
        if agent == "openai-api":
            rows.append(
                f"| {_installer_agent_label(agent)} | zip output only | "
                f"`dist/openai-api/zips/{RUNTIME_PROFILE}/` | none |"
            )
            continue
        for scope in SCOPE_ORDER:
            if (agent, scope) not in SOURCE_SKILL_ROOTS:
                continue
            if scope == "project":
                skill_target = f"<project>/{PROJECT_SKILL_SUBPATHS[agent].as_posix()}"
                profile_subpath = PROJECT_PROFILE_SUBPATHS.get(agent)
                profile_target = (
                    f"<project>/{profile_subpath.as_posix()}"
                    if profile_subpath is not None
                    else None
                )
            else:
                skill_target = _document_path(DEFAULT_SKILL_TARGETS[(agent, scope)])
                profile_path = DEFAULT_PROFILE_TARGETS.get((agent, scope))
                profile_target = (
                    _document_path(profile_path) if profile_path is not None else None
                )
            rows.append(
                f"| {_installer_agent_label(agent)} | `{scope}` | `{skill_target}` | "
                f"{f'`{profile_target}`' if profile_target is not None else 'none'} |"
            )
    return tuple(rows)


def _installation_matrix_rows(text: str) -> tuple[str, ...]:
    for table in _markdown_tables(text):
        data = table[1:]
        if data and all(
            len(row) == 4
            and (row[1] in {"`project`", "`user`", "`admin`", "zip output only"})
            for row in data
        ):
            return tuple(f"| {' | '.join(row)} |" for row in data)
    return ()


def _installation_contract_errors(root: Path) -> list[str]:
    """Validate docs projected from installers/changeforge_install.py."""

    errors: list[str] = []
    runtime_hosts = {agent for agent, _scope in SOURCE_SKILL_ROOTS}
    if runtime_hosts != set(INSTALLER_AGENTS) - {"openai-api"}:
        errors.append(
            f"{INSTALL_CONTRACT_SOURCE}: runtime host set diverges from installer agents"
        )
    profile_hosts = {agent for agent, _scope in SOURCE_PROFILE_ROOTS}
    if profile_hosts != {"codex", "claude", "copilot"}:
        errors.append(
            f"{INSTALL_CONTRACT_SOURCE}: static Agent Profile host set changed; "
            "update the documentation contract"
        )

    installation = root / "docs/INSTALLATION.md"
    if installation.is_file():
        text = installation.read_text(encoding="utf-8")
        actual_rows = _installation_matrix_rows(text)
        expected_rows = _expected_installation_matrix_rows()
        if actual_rows != expected_rows:
            errors.append(
                "docs/INSTALLATION.md: host/scope/default-target matrix must exactly "
                f"match {INSTALL_CONTRACT_SOURCE}"
            )

    return errors


def _required_content_errors(root: Path) -> list[str]:
    errors: list[str] = []
    requirements = {
        "docs/BUILD_PROFILES.md": (
            "Foundation and Domain Skills never enter Host top-level discovery",
            "Primary Professional routing happens once",
            "stable, independent Primary Route",
        ),
        "docs/VALIDATION.md": (
            "163-item projection once in a cleaned temporary directory",
            "Route Once behavior",
            *TEST_TIMEOUT_GUIDANCE_FACTS,
        ),
        "docs/SKILL_CONTENT_GOVERNANCE.md": (
            "strict order",
            "stable, independent Primary Route",
            "Foundation is a capability-modifier layer",
            "Domain is `modifier-only`",
        ),
    }
    for relative, phrases in requirements.items():
        path = root / relative
        if not path.is_file():
            continue
        text = _normalized_document_text(path.read_text(encoding="utf-8"))
        for phrase in phrases:
            if _normalized_document_text(phrase) not in text:
                errors.append(f"{relative}: missing required documentation content {phrase}")

    errors.extend(_installation_contract_errors(root))
    errors.extend(_layer3_cardinality_guidance_errors(root))
    return errors


def _ordered_command_errors(
    path: Path,
    commands: tuple[str, ...],
    label: str,
) -> list[str]:
    text = path.read_text(encoding="utf-8")
    position = 0
    errors: list[str] = []
    for command in commands:
        found = text.find(command, position)
        if found < 0:
            errors.append(
                f"{path.name}: missing or out-of-order {label} command {command}"
            )
            continue
        position = found + len(command)
        if text.count(command) != 1:
            errors.append(
                f"{path.name}: {label} command must appear exactly once {command}"
            )
    return errors


def _retired_workflow_contract_errors(root: Path) -> list[str]:
    """Reject retired workflow files and stale remote-execution requirements."""

    errors: list[str] = []
    for relative in RETIRED_WORKFLOW_PATHS:
        if (root / relative).exists():
            errors.append(f"retired workflow must remain absent: {relative}")

    for relative in RETIRED_WORKFLOW_CLAIM_DOCS:
        path = root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for claim in RETIRED_REMOTE_REQUIRED_CLAIMS:
            if claim.search(text):
                errors.append(
                    f"{relative}: retired remote-execution claim {claim.pattern}"
                )
    return errors
def _validation_path_consistency_errors(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in ("AGENTS.md", "docs/VALIDATION.md"):
        path = root / relative
        if not path.is_file():
            errors.append(f"missing validation path owner: {relative}")
            continue
        for commands, label in (
            (DEVELOPMENT_AFFECTED_COMMANDS, "Development Affected"),
            (FULL_REGRESSION_COMMANDS, "local Full Regression"),
        ):
            errors.extend(
                error.replace(path.name, relative, 1)
                for error in _ordered_command_errors(path, commands, label)
            )
    references = {
        "CONTRIBUTING.md": ("Development Affected", "docs/VALIDATION.md"),
        ".github/pull_request_template.md": (
            "local Full Regression",
            "docs/VALIDATION.md",
        ),
    }
    for relative, phrases in references.items():
        path = root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                errors.append(f"{relative}: missing validation path reference {phrase}")

    release = root / "docs/RELEASE.md"
    if release.is_file() and re.search(
        r"```(?:bash|sh)?\s+.*?python3 scripts/eval-core-principles\.py "
        r"--gate authoring.*?```",
        release.read_text(encoding="utf-8"),
        re.DOTALL,
    ):
        errors.append(
            "docs/RELEASE.md: must link to local Full Regression instead of "
            "duplicating its Core authoring command"
        )
    return errors


def _projection_section(
    text: str, heading: str
) -> tuple[str | None, str, list[str]]:
    errors: list[str] = []
    expression = re.compile(rf"(?m)^## {re.escape(heading)}[ \t]*$")
    matches = list(expression.finditer(text))
    if len(matches) != 1:
        return None, text, [f"section {heading!r} must appear exactly once"]
    match = matches[0]
    next_heading = re.search(r"(?m)^#{1,2} [^\n]+$", text[match.end() :])
    section_end = (
        match.end() + next_heading.start()
        if next_heading is not None
        else len(text)
    )
    body = text[match.end() : section_end].strip()
    outside = text[: match.start()] + text[section_end:]
    return body, outside, errors


def _core_projection_errors(
    root: Path, core_contracts: dict | None = None
) -> list[str]:
    errors: list[str] = []
    if core_contracts is None:
        try:
            core_contracts = load_core_contracts(
                root / "src" / "control-model" / "core-contracts.json"
            )
        except RuntimeError as exc:
            return [f"Core Model documentation contract is invalid: {exc}"]
    docs_contract = core_contracts["docs_contract"]
    for projection in docs_contract["projections"]:
        relative = projection["path"]
        path = root / relative
        if not path.is_file():
            errors.append(f"{relative}: missing Core Model documentation projection")
            continue
        text = path.read_text(encoding="utf-8")
        expected = docs_projection_block(core_contracts, projection)
        body, outside, section_errors = _projection_section(
            text, projection["section"]
        )
        errors.extend(f"{relative}: {error}" for error in section_errors)
        if body is not None and body != expected:
            errors.append(
                f"{relative}: docs projection {projection['id']!r} must equal "
                "the exact ordered Core Model rendering"
            )
        begin = (
            "<!-- BEGIN CHANGEFORGE CORE DOCS PROJECTION: "
            f"{projection['id']} -->"
        )
        end = (
            "<!-- END CHANGEFORGE CORE DOCS PROJECTION: "
            f"{projection['id']} -->"
        )
        if text.count(begin) != 1 or text.count(end) != 1:
            errors.append(
                f"{relative}: managed docs projection markers must each appear exactly once"
            )
        outside_folded = outside.casefold()
        completion = core_contracts["completion_state"]
        arrow_sources = [
            *completion["statuses"],
            *completion["fail_closed_rules"],
        ]
        arrow_expression = re.compile(
            rf"(?im)^\s*(?:{'|'.join(re.escape(item) for item in arrow_sources)})"
            r"\s*->"
        )
        if arrow_expression.search(outside):
            errors.append(
                f"{relative}: completion arrows are forbidden outside the managed projection"
            )
        for rule_id in completion["fail_closed_rules"]:
            if rule_id.casefold() in outside_folded:
                errors.append(
                    f"{relative}: fail-closed rule {rule_id!r} is duplicated outside "
                    "the managed projection"
                )
        field_declaration = re.compile(
            r"(?i)\b(?:extra\s+)?(?:task(?:\s+contract(?:\s+v2)?)?|"
            r"evidence(?:\s+ledger)?)\s+(?:fields?|schema|"
            r"(?:also\s+)?includes?|adds?|requires?)\b"
        )
        if field_declaration.search(outside):
            errors.append(
                f"{relative}: Task or Evidence field declarations are forbidden "
                "outside the managed projection"
            )
        if "runtime identity" in outside_folded:
            errors.append(
                f"{relative}: obsolete runtime identity is forbidden outside the "
                "managed projection"
            )
    for projection in docs_contract["context_budget_projections"]:
        relative = projection["path"]
        path = root / relative
        if not path.is_file():
            errors.append(f"{relative}: missing context budget documentation projection")
            continue
        text = path.read_text(encoding="utf-8")
        expected = context_budget_docs_projection_block(core_contracts, projection)
        body, _outside, section_errors = _projection_section(
            text, projection["section"]
        )
        errors.extend(f"{relative}: {error}" for error in section_errors)
        if body is not None and body != expected:
            errors.append(
                f"{relative}: context budget projection {projection['id']!r} must "
                "equal the exact Core Model rendering"
            )
        begin = (
            "<!-- BEGIN CHANGEFORGE CONTEXT BUDGET PROJECTION: "
            f"{projection['id']} -->"
        )
        end = (
            "<!-- END CHANGEFORGE CONTEXT BUDGET PROJECTION: "
            f"{projection['id']} -->"
        )
        if text.count(begin) != 1 or text.count(end) != 1:
            errors.append(
                f"{relative}: context budget projection markers must each appear exactly once"
            )
    return errors


def validate_docs_consistency(
    root: Path = ROOT,
    *,
    reports_dir: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_DOCS:
        if not (root / relative).is_file():
            errors.append(f"missing required documentation: {relative}")

    markdown = _markdown_files(root)
    for path in markdown:
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        errors.extend(_local_link_errors(root, path))
        for token in FORBIDDEN_USER_TOKENS:
            if token in text:
                errors.append(f"{relative}: obsolete user-path token {token}")
        for marker in DELETED_PATH_MARKERS:
            if marker in text and relative != "docs/MIGRATING_TO_HOOKLESS.md":
                errors.append(f"{relative}: references deleted source path {marker}")
        errors.extend(_command_target_errors(root, path))
        errors.extend(_current_term_errors(root, path))
        errors.extend(_shell_fence_placeholder_errors(root, path))

    errors.extend(_navigation_errors(root))
    errors.extend(_generated_document_ownership_errors(root))
    errors.extend(_required_content_errors(root))
    errors.extend(_runtime_surface_errors(root))
    errors.extend(_validation_path_consistency_errors(root))
    errors.extend(_retired_workflow_contract_errors(root))
    errors.extend(_volatile_fact_errors(root))
    errors.extend(_current_evidence_projection_errors(root))
    errors.extend(_host_product_surface_errors(root))
    errors.extend(_product_surface_errors(root))
    errors.extend(_release_process_errors(root))

    errors.extend(_core_projection_errors(root))
    try:
        governance_core = load_core_contracts(
            root / "src" / "control-model" / "core-contracts.json"
        )
    except RuntimeError:
        governance_core = None
    if governance_core is not None:
        errors.extend(
            _governance_context_budget_errors(
                root, governance_core, reports_dir
            )
        )
    errors.extend(_governance_evidence_freshness_errors(root))

    architecture = (root / "docs/HOOKLESS_ARCHITECTURE.md").read_text(encoding="utf-8")
    for phrase in ("Control Plane Prompt", "four Agent Profiles", "three Skill layers", "non-intercepting"):
        if phrase.casefold() not in architecture.casefold():
            errors.append(f"docs/HOOKLESS_ARCHITECTURE.md: missing {phrase}")
    subagent_model = (root / "docs/SUBAGENT_MODEL.md").read_text(encoding="utf-8")
    for phrase in ("main-control-agent", "analysis-agent", "task-agent", "review-agent"):
        if phrase.casefold() not in subagent_model.casefold():
            errors.append(f"docs/SUBAGENT_MODEL.md: missing {phrase}")
    authority_requirements = {
        "docs/BUILD_PROFILES.md": ("26", "163", "Runtime", "manifest"),
        "docs/INSTALLATION.md": ("scripts/build.py", "doctor", "manifest"),
        "docs/RELEASE.md": ("scripts/package.py", "Runtime build", "manifest"),
    }
    for relative, phrases in authority_requirements.items():
        text = (root / relative).read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase.casefold() not in text.casefold():
                errors.append(f"{relative}: missing packaging authority term {phrase}")
    return errors


def _args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--reports-dir", type=Path)
    args = parser.parse_args(argv)
    if args.reports_dir is None:
        args.reports_dir = Path(args.root) / "reports"
    return args


def main(argv: list[str] | None = None) -> int:
    args = _args(argv)
    errors = validate_docs_consistency(
        Path(args.root), reports_dir=args.reports_dir
    )
    if errors:
        for error in errors:
            print(f"validate-docs-consistency: ERROR: {error}", file=sys.stderr)
        return 1
    print(
        "validate-docs-consistency: validated "
        f"{len(_markdown_files(Path(args.root)))} current human-facing Markdown files; "
        f"{COMMAND_VALIDATION_SCOPE}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
