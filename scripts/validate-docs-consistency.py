#!/usr/bin/env python3
"""Validate documentation facts, generated-doc labels, and link consistency."""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import unquote

from validation_utils import (
    EXPECTED_FOUNDATION_CAPABILITY_COUNT,
    EXPECTED_PROFILE_TOP_LEVEL_COUNTS,
    load_yaml_file,
)


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_ROOTS = (
    "README.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "SECURITY.md",
    "SUPPORT.md",
    "CHANGELOG.md",
    "docs",
    "examples",
    "reports",
    "src/hook-runtime",
)
REPORT_MARKDOWN_ALLOWLIST = {
    "reports/README.md",
    "reports/public-benchmark-summary.md",
    "reports/professional-scorecard.md",
    "reports/codex-live-benchmark-summary.md",
    "reports/codex-current-home-smoke-summary.md",
}
EXCLUDED_MARKDOWN_PARTS = (
    ("reports", "codex-live-runs"),
    ("docs", "audits"),
)
COMMAND_DUPLICATION_EXCLUDES = {
    "docs/VALIDATION.md",
    "docs/SCORECARD_DASHBOARD.md",
    "docs/MARKETPLACE_CATALOG.md",
    "docs/SHOWCASE.md",
}
GENERATED_SNAPSHOT_FILES = (
    "docs/SCORECARD_DASHBOARD.md",
    "docs/MARKETPLACE_CATALOG.md",
    "docs/SHOWCASE.md",
    "reports/public-benchmark-summary.md",
    "reports/professional-scorecard.md",
    "reports/codex-live-benchmark-summary.md",
    "reports/codex-current-home-smoke-summary.md",
)
MARKETPLACE_WORDING_FILES = (
    "README.md",
    "docs/MARKETPLACE.md",
    "docs/MARKETPLACE_CATALOG.md",
)
BANNER_TERMS = (
    "generated",
    "do not edit by hand",
    "release snapshot",
    "regenerate",
    "scripts/",
)
STALE_PROFILE_TERMS = (
    "135 foundation",
    "19 top-level skill",
    "19 top level skill",
    "26 top-level skill",
    "26 top level skill",
)
STALE_HOOK_PHRASES = (
    "hooks opt-in",
    "hook opt-in",
    "executable hooks remain opt-in",
    "bootstrap by default",
    "default to warn, not block",
    "defaults to warn, not block",
    "codex and claude default to warn",
    "do not block codex or claude by default",
    "default mode is warn",
    "only changeforge_pre_edit_mode=block enables",
    "the default is warn and fail_open",
)
STOP_CLOSURE_ADVISORY_PATTERNS = (
    (
        "Stop closure is advisory by default",
        r"stop\s+closure\s+(?:is\s+)?advisory\s+by\s+default",
    ),
    (
        "Stop closure remains advisory by default",
        r"stop\s+closure\s+remains\s+advisory\s+by\s+default",
    ),
    (
        "Stop closure gaps remain advisory",
        r"stop\s+closure\s+gaps\s+remain\s+advisory",
    ),
    (
        "does not force continuation or block final handoff",
        r"does\s+not\s+force\s+continuation\s+or\s+block\s+final\s+handoff",
    ),
    (
        "records missing evidence as closure risk but does not block",
        r"records\s+missing\s+evidence\s+as\s+closure\s+risk.*does\s+not\s+.*block",
    ),
)
LICENSE_STALE_MARKERS = (
    "proprietary",
    "owner decision required before open-source publication",
    "selected_license remains null",
    "no root license is added",
    "must choose an osi-approved license before publishing",
    "license decision pending",
    "pending owner decision",
    "owner license decision",
    "owner decisions are not complete",
    "not publishable as an open-source project until",
    "not publishable as open source until",
)
MIT_LICENSE_MARKERS = (
    "MIT License",
    "Permission is hereby granted, free of charge",
    'THE SOFTWARE IS PROVIDED "AS IS"',
)
VALIDATION_COMMAND_RE = re.compile(
    r"^\s*python3\s+(?:-m\s+unittest|scripts/(?:validate-|eval-|build\.py|run-codegen|generate-))"
)
VALIDATION_COMMAND_BLOCK_RE = re.compile(
    r"\bpython3(?:\s|\\\s*\n)+"
    r"(?:-m(?:\s|\\\s*\n)+unittest|scripts/(?:validate-|eval-|build\.py|run-codegen|generate-))",
    re.IGNORECASE,
)
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def _rel(root: Path, path: Path) -> str:
    return str(path.relative_to(root))


def _is_excluded(root: Path, path: Path) -> bool:
    rel_parts = path.relative_to(root).parts
    return any(rel_parts[: len(parts)] == parts for parts in EXCLUDED_MARKDOWN_PARTS)


def iter_markdown_files(root: Path) -> list[Path]:
    """Return markdown files covered by documentation consistency checks."""
    files: list[Path] = []
    for entry in MARKDOWN_ROOTS:
        path = root / entry
        if path.is_file() and path.suffix == ".md":
            files.append(path)
        elif path.is_dir():
            for candidate in sorted(path.rglob("*.md")):
                rel = str(candidate.relative_to(root))
                if rel.startswith("reports/") and rel not in REPORT_MARKDOWN_ALLOWLIST:
                    continue
                if not _is_excluded(root, candidate):
                    files.append(candidate)
    return sorted(dict.fromkeys(files))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _profile_count_errors(root: Path, markdown_files: list[Path]) -> list[str]:
    errors: list[str] = []
    expected = EXPECTED_PROFILE_TOP_LEVEL_COUNTS
    for path in markdown_files:
        rel = _rel(root, path)
        text = _read(path)
        lowered = text.casefold()
        for term in STALE_PROFILE_TERMS:
            if term in lowered:
                errors.append(f"{rel}: stale profile count phrase: {term}")

        for profile, count in re.findall(r"\b(recommended|full|dev)\s*=\s*(\d+)\b", text):
            actual = int(count)
            if actual != expected[profile]:
                errors.append(f"{rel}: {profile}={actual} conflicts with expected {expected[profile]}")

        for profile, count in re.findall(r"\b(recommended|full|dev)\s+top-level count is (\d+)", text, re.IGNORECASE):
            expected_count = expected[profile.lower()]
            actual = int(count)
            if actual != expected_count:
                errors.append(
                    f"{rel}: {profile.lower()} top-level count {actual} conflicts with expected {expected_count}"
                )

        foundation_matches = re.findall(r"(\d+)\s+foundation capabilit", text, re.IGNORECASE)
        for value in foundation_matches:
            actual = int(value)
            if actual != EXPECTED_FOUNDATION_CAPABILITY_COUNT:
                errors.append(
                    f"{rel}: foundation capability count {actual} conflicts with expected "
                    f"{EXPECTED_FOUNDATION_CAPABILITY_COUNT}"
                )
    return errors


def _hook_default_errors(root: Path, markdown_files: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in markdown_files:
        rel = _rel(root, path)
        lines = _read(path).splitlines()
        for number, line in enumerate(lines, start=1):
            lowered = line.casefold()
            normalized = re.sub(r"[`\s]+", " ", lowered).strip()
            for phrase in STALE_HOOK_PHRASES:
                pattern = rf"(?<![\w-]){re.escape(phrase)}(?![\w-])"
                if re.search(pattern, normalized):
                    errors.append(f"{rel}:{number}: stale hook default phrase: {phrase}")
            if "--with-hooks" not in line:
                continue
            required_like = re.search(r"\b(required|default|must|need(?:ed)? to specify|explicitly specify)\b", lowered)
            allowed_context = (
                "backward-compatible" in lowered
                or "backward compatible" in lowered
                or "accepted" in lowered
                or "no longer required" in lowered
                or "users no longer need" in lowered
            )
            if required_like and not allowed_context:
                errors.append(f"{rel}:{number}: --with-hooks is described as required/default")
    return errors


def _stop_closure_default_errors(root: Path, markdown_files: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in markdown_files:
        rel = _rel(root, path)
        lines = _read(path).splitlines()
        for number, line in enumerate(lines, start=1):
            normalized = re.sub(r"[`\s]+", " ", line.casefold()).strip()
            for label, pattern in STOP_CLOSURE_ADVISORY_PATTERNS:
                if re.search(pattern, normalized):
                    errors.append(f"{rel}:{number}: stale Stop closure advisory-default phrase: {label}")
            if "stop closure follows the stop closure policy on supported events" in normalized:
                context = " ".join(lines[max(0, number - 3) : min(len(lines), number + 2)]).casefold()
                if not (
                    "block" in context
                    or "degraded" in context
                    or "unsupported" in context
                ):
                    errors.append(
                        f"{rel}:{number}: Stop closure policy sentence must state block/degraded default"
                    )
    return errors


def _validation_command_count(text: str) -> int:
    return len(VALIDATION_COMMAND_BLOCK_RE.findall(text))


def _fenced_code_blocks(text: str) -> list[tuple[int, str]]:
    blocks: list[tuple[int, str]] = []
    in_block = False
    start = 0
    collected: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            if in_block:
                blocks.append((start, "\n".join(collected)))
                collected = []
                in_block = False
            else:
                in_block = True
                start = number
                collected = []
            continue
        if in_block:
            collected.append(line)
    return blocks


def _validation_command_duplication_errors(root: Path, markdown_files: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in markdown_files:
        rel = _rel(root, path)
        if rel in COMMAND_DUPLICATION_EXCLUDES or rel.startswith("reports/"):
            continue
        text = _read(path)
        for start, code in _fenced_code_blocks(text):
            command_count = _validation_command_count(code)
            if command_count >= 10:
                errors.append(
                    f"{rel}:{start}: duplicated validation command fenced block has {command_count} commands"
                )
        run_start = 0
        run_length = 0
        for number, line in enumerate(text.splitlines(), start=1):
            if VALIDATION_COMMAND_RE.match(line):
                if run_length == 0:
                    run_start = number
                run_length += 1
            else:
                if run_length >= 10:
                    errors.append(f"{rel}:{run_start}: duplicated validation command block has {run_length} lines")
                run_length = 0
        if run_length >= 10:
            errors.append(f"{rel}:{run_start}: duplicated validation command block has {run_length} lines")
    return errors


def _hook_policy_consistency_errors(root: Path) -> list[str]:
    errors: list[str] = []
    policy_path = root / "src" / "hook-runtime" / "scripts" / "changeforge_hook_policy.py"
    if not policy_path.exists():
        return ["src/hook-runtime/scripts/changeforge_hook_policy.py: missing hook policy source"]
    policy = _read(policy_path)
    policy_checks = (
        ("DEFAULT_GATE_MODES", r"\bDEFAULT_GATE_MODES\b"),
        ('"sdd_material_choice": "block"', r"['\"]sdd_material_choice['\"]\s*:\s*['\"]block['\"]"),
        ('"pre_edit_structure": "block"', r"['\"]pre_edit_structure['\"]\s*:\s*['\"]block['\"]"),
        ('"process_phase": "block"', r"['\"]process_phase['\"]\s*:\s*['\"]block['\"]"),
        ('"stop_closure": "block"', r"['\"]stop_closure['\"]\s*:\s*['\"]block['\"]"),
        (
            'DEFAULT_GATE_MODES.get(gate_key, "warn")',
            r"DEFAULT_GATE_MODES\.get\(\s*gate_key\s*,\s*['\"]warn['\"]\s*\)",
        ),
        ('global_failure or "fail_open"', r"global_failure\s+or\s+['\"]fail_open['\"]"),
    )
    for label, pattern in policy_checks:
        if not re.search(pattern, policy):
            errors.append(f"{policy_path.relative_to(root)}: missing hook policy fact: {label}")
    doc_checks = (
        (
            "SDD material choice defaults to block",
            lambda text: (
                ("sdd material choice" in text or "sdd_material_choice=block" in text)
                and "default" in text
                and "block" in text
            ),
        ),
        (
            "pre-edit structure defaults to block",
            lambda text: (
                (
                    "pre-edit structure" in text
                    or "pre edit structure" in text
                    or "pre_edit_structure=block" in text
                )
                and "default" in text
                and "block" in text
            ),
        ),
        (
            "process phase defaults to block",
            lambda text: (
                (
                    "process phase" in text
                    or "process_phase=block" in text
                    or "process_phase: block" in text
                )
                and "default" in text
                and "block" in text
            ),
        ),
        (
            "Stop closure blocks where supported and degrades when unsupported",
            lambda text: (
                "stop closure" in text
                and "default" in text
                and "block" in text
                and ("degraded" in text or "unsupported" in text or "cannot enforce" in text)
            ),
        ),
        (
            "unspecified or ordinary advisory gates fallback to warn",
            lambda text: (
                "unspecified gates fallback to warn" in text
                or "ordinary advisory gates default to warn" in text
                or "ordinary advisory context defaults to warn" in text
                or "unspecified gates fallback warn" in text
            ),
        ),
        (
            "failures default to fail_open",
            lambda text: (
                "failure mode defaults to fail_open" in text
                or "failures default to fail_open" in text
                or "hook failures default to fail_open" in text
                or "hook runtime failures still fail open" in text
            ),
        ),
    )
    for rel in ("docs/HOOKS.md", "src/hook-runtime/README.md"):
        path = root / rel
        if not path.exists():
            errors.append(f"{rel}: missing hook policy documentation")
            continue
        text = re.sub(r"[`\s]+", " ", _read(path).casefold()).strip()
        for label, predicate in doc_checks:
            if not predicate(text):
                errors.append(f"{rel}: missing hook policy fact: {label}")
    return errors


def _pyproject_license_text(root: Path) -> str:
    path = root / "pyproject.toml"
    if not path.exists():
        return ""
    try:
        parsed = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return ""
    project = parsed.get("project", parsed)
    license_value = project.get("license") if isinstance(project, dict) else None
    if isinstance(license_value, dict):
        return str(license_value.get("text") or license_value.get("file") or "").strip()
    if isinstance(license_value, str):
        return license_value.strip()
    return ""


def _license_consistency_errors(root: Path, markdown_files: list[Path]) -> list[str]:
    errors: list[str] = []
    license_path = root / "LICENSE"
    if not license_path.exists():
        errors.append("LICENSE: missing root MIT license file")
    else:
        license_text = _read(license_path)
        for marker in MIT_LICENSE_MARKERS:
            if marker not in license_text:
                errors.append(f"LICENSE: missing MIT license marker: {marker}")

    pyproject_path = root / "pyproject.toml"
    pyproject_text = _read(pyproject_path) if pyproject_path.exists() else ""
    pyproject_license = _pyproject_license_text(root)
    if "proprietary" in pyproject_text.casefold():
        errors.append("pyproject.toml: must not contain Proprietary license metadata")
    if pyproject_license != "MIT":
        errors.append("pyproject.toml: project license must be MIT")

    config_path = root / "config" / "open-source-release.yaml"
    config = load_yaml_file(config_path) if config_path.exists() else {}
    if not config_path.exists():
        errors.append("config/open-source-release.yaml: missing open-source release config")
    if config.get("selected_license") != "MIT":
        errors.append("config/open-source-release.yaml: selected_license must be MIT")
    if config.get("contribution_licensing_confirmed") is not True:
        errors.append(
            "config/open-source-release.yaml: contribution_licensing_confirmed must be true"
        )
    if config.get("security_contact_confirmed") is not True:
        errors.append("config/open-source-release.yaml: security_contact_confirmed must be true")

    for path in markdown_files:
        rel = _rel(root, path)
        for number, line in enumerate(_read(path).splitlines(), start=1):
            lowered = line.casefold()
            for marker in LICENSE_STALE_MARKERS:
                if marker in lowered:
                    errors.append(f"{rel}:{number}: stale license/open-source readiness phrase: {marker}")
    return errors


def _release_gate_anchor_errors(root: Path, markdown_files: list[Path]) -> list[str]:
    errors: list[str] = []
    validation = root / "docs" / "VALIDATION.md"
    validation_has_release_gate = (
        validation.exists() and re.search(r"^##\s+Release Gate\s*$", _read(validation), re.MULTILINE)
    )
    validation_referenced_from_release_gate = False
    link_required = {"docs/README.md", "docs/RELEASE.md", "docs/OPEN_SOURCE_READINESS.md"}
    for path in markdown_files:
        rel = _rel(root, path)
        text = _read(path)
        lowered = text.casefold()
        if "release gate" in lowered and "validation.md" in lowered:
            validation_referenced_from_release_gate = True
            if rel in link_required and "validation.md#release-gate" not in lowered:
                errors.append(f"{rel}: Release Gate reference must link to VALIDATION.md#release-gate")
    if validation_referenced_from_release_gate and not validation_has_release_gate:
        errors.append("docs/VALIDATION.md: missing ## Release Gate section referenced by docs")
    return errors


def _generated_banner_errors(root: Path) -> list[str]:
    errors: list[str] = []
    for rel in GENERATED_SNAPSHOT_FILES:
        path = root / rel
        if not path.exists():
            continue
        lowered = _read(path).casefold()
        if not any(term in lowered for term in BANNER_TERMS):
            errors.append(f"{rel}: generated/snapshot banner is missing")
    return errors


def _marketplace_claim_errors(root: Path, markdown_files: list[Path]) -> list[str]:
    errors: list[str] = []
    official_claim_re = re.compile(
        r"\bofficial\b[^\n]{0,80}\b(?:marketplace)\b[^\n]{0,80}\b(?:available|published|live|launched)\b",
        re.IGNORECASE,
    )
    for path in markdown_files:
        rel = _rel(root, path)
        for number, line in enumerate(_read(path).splitlines(), start=1):
            lowered = line.casefold()
            if official_claim_re.search(line) and "not" not in lowered:
                errors.append(f"{rel}:{number}: unsupported official marketplace publication claim")

    for rel in MARKETPLACE_WORDING_FILES:
        path = root / rel
        if not path.exists():
            continue
        text = _read(path).casefold()
        has_local = "local discovery" in text or "local/source-derived" in text or "source-derived discovery" in text
        has_official_boundary = "official" in text and "not implemented" in text
        if not has_local:
            errors.append(f"{rel}: must say marketplace/catalog is local/source-derived discovery only")
        if not has_official_boundary:
            errors.append(f"{rel}: must say official marketplace publishing is not implemented")
    return errors


def _open_source_blocked(root: Path) -> bool:
    config_path = root / "config" / "open-source-release.yaml"
    config = load_yaml_file(config_path) if config_path.exists() else {}
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8") if (root / "pyproject.toml").exists() else ""
    return not (
        (root / "LICENSE").exists()
        and bool(config.get("selected_license"))
        and config.get("contribution_licensing_confirmed") is True
        and config.get("security_contact_confirmed") is True
        and "proprietary" not in pyproject.casefold()
    )


def _open_source_claim_errors(root: Path, markdown_files: list[Path]) -> list[str]:
    errors: list[str] = []
    if not _open_source_blocked(root):
        return errors
    banned_claim_re = re.compile(
        r"\b(?:fully\s+open-source-ready|fully\s+open source ready|ready for open-source publication|ready for open source publication)\b",
        re.IGNORECASE,
    )
    for path in markdown_files:
        rel = _rel(root, path)
        for number, line in enumerate(_read(path).splitlines(), start=1):
            if banned_claim_re.search(line):
                errors.append(f"{rel}:{number}: overstates open-source readiness while owner decisions are incomplete")

    readiness = root / "docs" / "OPEN_SOURCE_READINESS.md"
    if readiness.exists():
        text = _read(readiness).casefold()
        if "not publishable" not in text:
            errors.append("docs/OPEN_SOURCE_READINESS.md: must state repository is not publishable as open source")
        if "owner" not in text or "license" not in text:
            errors.append("docs/OPEN_SOURCE_READINESS.md: must name owner license/security decisions")
    return errors


def _strip_link_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if " " in target and not target.startswith("<"):
        target = target.split(" ", 1)[0]
    return target.split("#", 1)[0]


def _markdown_link_errors(root: Path, markdown_files: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in markdown_files:
        rel = _rel(root, path)
        text = _read(path)
        for match in LINK_RE.finditer(text):
            raw_target = match.group(1)
            if raw_target.startswith(("#", "http://", "https://", "mailto:", "file:")):
                continue
            target_text = _strip_link_target(raw_target)
            if not target_text:
                continue
            target = (path.parent / unquote(target_text)).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                errors.append(f"{rel}: link points outside repository: {raw_target}")
                continue
            if not target.exists():
                errors.append(f"{rel}: missing local link target: {target.relative_to(root)}")
    return errors


def validate_docs_consistency(root: Path) -> list[str]:
    """Return documentation consistency errors for the repository."""
    root = root.resolve()
    markdown_files = iter_markdown_files(root)
    errors: list[str] = []
    errors.extend(_profile_count_errors(root, markdown_files))
    errors.extend(_hook_default_errors(root, markdown_files))
    errors.extend(_stop_closure_default_errors(root, markdown_files))
    errors.extend(_hook_policy_consistency_errors(root))
    errors.extend(_license_consistency_errors(root, markdown_files))
    errors.extend(_release_gate_anchor_errors(root, markdown_files))
    errors.extend(_validation_command_duplication_errors(root, markdown_files))
    errors.extend(_generated_banner_errors(root))
    errors.extend(_marketplace_claim_errors(root, markdown_files))
    errors.extend(_open_source_claim_errors(root, markdown_files))
    errors.extend(_markdown_link_errors(root, markdown_files))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args(argv)
    errors = validate_docs_consistency(Path(args.root))
    if errors:
        for error in errors:
            print(f"validate-docs-consistency: ERROR: {error}", file=sys.stderr)
        return 1
    print("validate-docs-consistency: documentation facts are consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
